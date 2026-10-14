import symbolsPsp from './data/Persona Symbol System.json';
import symbolsPs1 from './data/Persona Symbol System PS1.json';
import personaNames from './data/Persona ID.json';
import charactersPsp from './data/Characters.json';
import charactersRevelations from './data/Characters (Revalations).json';
import locations from './data/Locations (PSP).json';
import warps from './data/Warps (PSP).json';

const pspCharacterByCode = Object.fromEntries(Object.entries(symbolsPsp).map(([character, code]) => [code.toLowerCase(), character]));
const ps1CharacterByCode = Object.fromEntries(Object.entries(symbolsPs1).filter(([character]) => character.length === 1).map(([character, code]) => [code.toLowerCase(), character]));
const cleanName = value => String(value ?? '').replace(/[\0\xff]/g, '').trim();
const hexByte = value => value.toString(16).padStart(2, '0');
const decodePspName = (bytes, offset, width = 8) => {
  let name = '';
  for (let i = 0; i < width; i++) {
    const code = `${hexByte(bytes[offset + i * 2])}${hexByte(bytes[offset + i * 2 + 1])}`;
    if (code === '0000' || code === 'ffff') break;
    name += pspCharacterByCode[code] || '?';
  }
  return cleanName(name);
};
const encodePs1Name = (name, width, terminated = true, uppercase = false) => {
  const text = Array.from(cleanName(uppercase ? String(name ?? '').toUpperCase() : name)).slice(0, width);
  const result = text.map(character => Number.parseInt(symbolsPs1[character] || '00', 16));
  if (terminated && result.length < width) result.push(0xff);
  while (result.length < width) result.push(0);
  return result;
};
const encodePs1NameEntry = (name, variant) => {
  if (variant === 'US') return new Array(10).fill(0);
  const characters = encodePs1Name(name, 5, false, true);
  return characters.flatMap(character => [0x80, character]);
};
const readLE = (bytes, offset, width = 4) => {
  let value = 0;
  for (let i = width - 1; i >= 0; i--) value = value * 256 + (bytes[offset + i] || 0);
  return value;
};
const writeLE = (bytes, offset, value, width = 4) => {
  let current = Number(value) >>> 0;
  for (let i = 0; i < width; i++) { bytes[offset + i] = current & 255; current >>>= 8; }
};
const decodePs1Name = (bytes, offset, width = 8) => {
  let name = '';
  for (let i = 0; i < width && offset + i < bytes.length; i++) {
    const code = bytes[offset + i];
    if (code === 0xff) break;
    name += code === 0 ? ' ' : ps1CharacterByCode[hexByte(code)] || '?';
  }
  return cleanName(name);
};
const decodePs1NameEntry = (bytes, offset, width = 5) => {
  let name = '';
  for (let i = 0; i < width; i++) {
    const first = bytes[offset + i * 2], second = bytes[offset + i * 2 + 1];
    if (second === 0xff || first === 0xff) break;
    const code = first === 0x80 ? second : first;
    if (code !== 0 && code !== 0x80) name += ps1CharacterByCode[hexByte(code)] || '?';
  }
  return cleanName(name);
};
const encodePspName = (name, width = 8, terminated = true) => {
  const characters = Array.from(cleanName(name)).slice(0, width), result = [];
  for (const character of characters) {
    const code = symbolsPsp[character] || '0000';
    result.push(Number.parseInt(code.slice(0, 2), 16), Number.parseInt(code.slice(2, 4), 16));
  }
  if (terminated && characters.length < width) result.push(0xff, 0xff);
  while (result.length < width * 2) result.push(0, 0);
  return result;
};

/** Convert a PS1 save payload into the shared PC/PSP payload used by the editor. */
export function convertPs1ToCanonical(core, variant = 'US', options = {}) {
  if (!(core instanceof Uint8Array) || core.length !== 14336) throw new Error('PS1 conversion requires a 14,336-byte save payload.');
  if (!['US', 'JP', 'JPCONT'].includes(variant)) throw new Error('Choose a supported PS1 source region.');
  const nickname = decodePs1Name(core, 191, 8);
  const lastName = options.lastName ?? decodePs1NameEntry(core, 3649, 5);
  const firstName = options.firstName ?? decodePs1NameEntry(core, 3659, 5);
  const chunks = [];
  const append = bytes => chunks.push(bytes);
  const slice = (start, end) => core.slice(start, end);

  // Main character record.
  append(Uint8Array.from([...slice(128, 191), 0, ...encodePspName(nickname), ...new Array(22).fill(0)]));
  append(Uint8Array.from([...slice(199, 216), 0]));
  append(slice(216, 224));
  // Four teammate records and translated display names.
  for (let teammate = 0; teammate < 4; teammate++) {
    const base = 224 + teammate * 96, nameOffset = 287 + teammate * 96, id = core[286 + teammate * 96];
    let name = decodePs1Name(core, nameOffset, 8);
    if (options.teammateNames === 'revelations') name = cleanName((options.charactersCatalog||charactersRevelations)[hexByte(id)] || name);
    if (options.teammateNames === 'psp-defaults') name = cleanName((options.charactersCatalog||charactersPsp)[hexByte(id)] || name);
    append(Uint8Array.from([...slice(base, base + 63), 0, ...(id ? encodePspName(name) : new Array(16).fill(0)), ...new Array(22).fill(0)]));
    append(Uint8Array.from([...slice(base + 71, base + 88), 0]));
    append(slice(base + 89, base + 97));
  }
  // Persona records are expanded to the 100-byte PSP record size.
  for (let persona = 0; persona < 31; persona++) {
    const base = 608 + persona * 64;
    append(Uint8Array.from([...slice(base, base + 25), ...new Array(41).fill(0)]));
    append(Uint8Array.from([...slice(base + 33, base + 64), ...new Array(3).fill(0)]));
  }
  append(Uint8Array.from([...new Array(96).fill(0), 0xff, 0, 0, 0]));
  append(slice(2592, 2616));
  for (let form = 8; form >= 0; form--) append(slice(2616 + form * 25, 2616 + (form + 1) * 25));
  append(Uint8Array.from([...slice(2841, 3632), ...new Array(256).fill(0)]));
  append(slice(3632, 3648));
  append(Uint8Array.from([...encodePspName(lastName, 8, false), ...encodePspName(firstName, 8, false), ...new Array(8).fill(0), ...encodePspName(nickname), ...new Array(8).fill(0)]));
  append(Uint8Array.from([...slice(3684, 3692), ...new Array(8).fill(0), 3, 0, 0, 0]));

  let locationId = `${hexByte(core[3692])}${hexByte(core[3693])}`;
  let locationEntry = Object.entries(locations).find(([, entry]) => entry[0] === locationId);
  if (!locationEntry) { locationEntry = ['4', locations['4']]; locationId = '3b02'; }
  const [locationKey, entry] = locationEntry;
  append(Uint8Array.from([Number.parseInt(locationId.slice(0, 2), 16), Number.parseInt(locationId.slice(2, 4), 16), ...new Array(94).fill(0)]));
  append(slice(3708, 3757));
  append(Uint8Array.from([...new Array(13951).fill(0), 0x78, 0x56, 0x34, 0x12]));

  const output = new Uint8Array(19336);
  let cursor = 0;
  for (const chunk of chunks) { if (cursor + chunk.length > output.length) throw new Error('PS1 conversion produced an oversized payload.'); output.set(chunk, cursor); cursor += chunk.length; }
  if (cursor !== output.length) throw new Error(`PS1 conversion produced ${cursor} bytes; expected ${output.length}.`);

  // Transfer analyze data, time, location coordinates, and game-specific fixes.
  output.set(core.subarray(3836, 3856), 5588);
  const seconds = core[9] * 3600 + core[10] * 60 + core[11];
  writeLE(output, 17692, seconds);
  const fields = [[2, 5300], [3, 5302], [4, 5304], [5, 5306], [6, 5308]];
  for (const [entryIndex, offset] of fields) {
    const value = entry[entryIndex] || '0000';
    output[offset] = Number.parseInt(value.slice(0, 2), 16);
    output[offset + 1] = Number.parseInt(value.slice(2, 4), 16);
  }
  output[5240] = output[5302]; output[5241] = output[5303];
  output[5244] = output[5304]; output[5245] = output[5305];
  output[5248] = output[5306]; output[5249] = output[5307];
  output[5418] = 1; output[19192] = 1;
  if (variant === 'US' && options.convertMoney !== false) writeLE(output, 4104, readLE(output, 4104) * 100);
  return output;
}

/** Convert the shared PC/PSP save layout into the PS1-specific payload layout. */
export function convertCanonicalToPs1(core, variant = 'US', options = {}) {
  if (!(core instanceof Uint8Array) || core.length < 14336) throw new Error('PS1 conversion requires a complete 14,336-byte PC/PSP save payload.');
  if (!['US', 'JP', 'JPCONT'].includes(variant)) throw new Error('Choose a supported PS1 target region.');
  const source = core.subarray(0, 14336);
  const uppercase = variant !== 'US';
  const tagSource = options.tagSource || 'nickname';
  const tagOffset = tagSource === 'last' ? 5152 : tagSource === 'first' ? 5168 : tagSource === 'nickname' ? 64 : 5192;
  const nickname = tagSource === 'custom'
    ? encodePs1Name(options.customTag || '', 8, true, uppercase)
    : encodePs1Name(decodePspName(source, tagOffset), 8, true, uppercase);
  const firstName = encodePs1NameEntry(options.firstName || '', variant);
  const lastName = encodePs1NameEntry(options.lastName || '', variant);
  const chunks = [];
  const append = bytes => chunks.push(bytes);
  const slice = (start, end) => source.slice(start, end);

  // PS1 save header metadata: transferred name, level, and play-time display.
  const seconds = options.seconds ?? (core.length>=19336?readLE(core,17692):0);
  let hours = Math.floor(seconds / 3600), minutes = Math.floor((seconds % 3600) / 60), secs = seconds % 60;
  if (hours > 99) { hours = 99; minutes = 59; }
  append(Uint8Array.from([...nickname, source[106], hours, minutes, secs, 0, ...new Array(115).fill(0)]));

  // Main character block and the four companion blocks.
  append(Uint8Array.from([...slice(0, 63), ...nickname]));
  append(slice(102, 119));
  append(slice(120, 128));
  for (let companion = 0; companion < 4; companion++) {
    const base = 128 + companion * 128;
    const characterId = source[base + 62];
    let companionName = decodePspName(source, 192 + companion * 256);
    if (options.teammateNames === 'revelations') companionName = cleanName(charactersRevelations[hexByte(characterId)] || companionName);
    if (options.teammateNames === 'psp-defaults') companionName = cleanName(charactersPsp[hexByte(characterId)] || companionName);
    append(Uint8Array.from([...slice(base, base + 63), ...(characterId ? encodePs1Name(companionName, 8, true, uppercase) : new Array(8).fill(0))]));
    append(slice(base + 102, base + 119));
    append(slice(base + 120, base + 128));
  }

  // Persona records carry localized display names in the PS1 data layout.
  for (let persona = 0; persona < 31; persona++) {
    const base = 640 + persona * 100;
    const id = source[base + 24];
    append(slice(base, base + 25));
    const name = cleanName((options.personaCatalog||personaNames)[hexByte(id)] || '');
    append(Uint8Array.from(id ? encodePs1Name(name, 10, true, uppercase) : new Array(10).fill(0)));
    append(slice(base + 68, base + 97));
  }

  // Compendium, form records, inventory and other common blocks.
  append(slice(3840, 3864));
  if (options.importFormData) {
    for (let i = 8; i >= 0; i--) append(slice(3864 + i * 25, 3864 + (i + 1) * 25));
  } else {
    const partySlots = Array.from(source.subarray(3840, 3845)).filter(value => value !== 0xff).length;
    const form = new Uint8Array(25).fill(0xff);
    for (let i = 0; i < partySlots; i++) { form[i * 2] = i; form[i * 2 + 1] = 0xff; }
    for (let i = 0; i < 9; i++) append(form);
  }
  append(slice(4089, 4880));
  append(slice(5136, 5152));
  append(Uint8Array.from([...lastName, ...firstName, ...nickname, ...new Array(8).fill(0)]));
  append(slice(5216, 5224));

  // Translate the PSP location ID to the corresponding PS1 map ID.
  const locationId = `${hexByte(source[5236])}${hexByte(source[5237])}`;
  let ps1Location = Object.values(locations).find(entry => entry[0] === locationId)?.[7];
  if (!ps1Location) ps1Location = Object.values(warps).find(entry => entry[0] === locationId)?.[2];
  if (ps1Location === '4800' && source[5240] === 1) ps1Location = '4900';
  if (readLE(source, 5232, 2) === 2 || !ps1Location) ps1Location = '3b02';
  append(Uint8Array.from([Number.parseInt(ps1Location.slice(0, 2), 16), Number.parseInt(ps1Location.slice(2, 4), 16)]));
  append(Uint8Array.from([...new Array(14).fill(0), ...slice(5332, 5381)]));
  append(new Uint8Array(10579));

  const output = new Uint8Array(14336);
  let cursor = 0;
  for (const chunk of chunks) { output.set(chunk.subarray(0, Math.max(0, output.length - cursor)), cursor); cursor += chunk.length; }
  // The reference assembler produces a short tail; the target save payload keeps the fixed PC/PS1 size.
  if (cursor > output.length) throw new Error('PS1 conversion produced an oversized save payload.');
  // The US PS1 version stores money in hundreds; other regions share the PC/PSP unit.
  if (variant === 'US' && options.convertMoney !== false) {const money=readLE(source,4104)/100,lower=Math.floor(money),fraction=money-lower,rounded=fraction<0.5?lower:fraction>0.5?lower+1:lower%2===0?lower:lower+1;writeLE(output,2856,rounded);}
  const hoursTag = Math.min(99, Math.floor(seconds / 3600));
  const minutesTag = Math.min(hoursTag === 99 ? 59 : 59, Math.floor((seconds % 3600) / 60));
  const secondsTag = seconds % 60;
  output.set([hoursTag, minutesTag, secondsTag, 0], 3696);
  output.set(source.subarray(5588, 5608), 3836);
  return output;
}

/** Convert a PC raw save through the shared PS1 layout into the expanded PSP layout. */
export function convertPcToPsp(core, options = {}) {
  if (!(core instanceof Uint8Array) || core.length < 14336) throw new Error('PC-to-PSP conversion requires a complete 14,336-byte PC save.');
  const ps1 = convertCanonicalToPs1(core, 'JP', {
    firstName: options.firstName ?? decodePspName(core, 5168),
    lastName: options.lastName ?? decodePspName(core, 5152),
    teammateNames: options.teammateNames ?? 'transfer',
    charactersCatalog: options.charactersCatalog,
    personaCatalog: options.personaCatalog,
    seconds: options.seconds,
    tagSource: 'nickname',
    importFormData: true,
  });
  const psp = convertPs1ToCanonical(ps1, 'JP', {
    firstName: options.firstName ?? decodePspName(core, 5168),
    lastName: options.lastName ?? decodePspName(core, 5152),
    teammateNames: options.teammateNames ?? 'transfer',
    charactersCatalog: options.charactersCatalog,
    personaCatalog: options.personaCatalog,
    importFormData: true,
  });
  psp.set(encodePspName(options.lastName ?? decodePspName(core, 5152), 8, false), 5152);
  psp.set(encodePspName(options.firstName ?? decodePspName(core, 5168), 8, false), 5168);
  if (options.seconds !== undefined) writeLE(psp, 17692, options.seconds);
  if (options.difficulty !== undefined) {
    const difficulty = Number(options.difficulty);
    if (!Number.isInteger(difficulty) || difficulty < 0 || difficulty > 2) throw new Error('Difficulty must be 0, 1, or 2.');
    psp[17560] = difficulty;
  }
  return psp;
}
