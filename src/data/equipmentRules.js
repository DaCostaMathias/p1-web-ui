// Persona 1 equipment restrictions and realistic value caps.
// Sources: Megami Tensei Wiki (Battle Stats), persona1.wikidot.com,
// atwiki persona1 (PSP/装備品/武器 and 銃), wikiwiki.jp persona pages.
// Equipment slot indices on the save: 0 weapon, 1 gun, 2 ammo, 3 helmet, 4 body, 5 arm, 6 leg.

// Hard caps used by the game UI (HP/SP top out at 999, stats at 99).
export const partyLimits = {
  level: 99,
  personaLevel: 99,
  hp: 999,
  sp: 999,
  stat: 99,          // STR / VIT / TEC / AGI / LUK base cap
  addedStat: 99,     // added-stat byte caps at 99 just like the base stat
  weaponAtk: 255,    // weapon ATK display value (byte-sized)
  weaponAcc: 255,
  gunAtk: 255,
  gunAcc: 255,
  experience: 9999999,
  personaExperience: 9999999,
};

// Which melee / gun class each playable character may wield.
export const weaponTypeByCharacter = {
  1: 'sword1h',    // MC
  2: 'bow',        // Maki
  3: 'spear',      // Brown
  4: 'sword2h',    // Nanjo
  5: 'axe',        // Mark
  6: 'sword1h',    // Elly
  7: 'whip',       // Ayase
  8: 'thrown',     // Yukino
  9: 'fists',      // Reiji
};

export const gunTypeByCharacter = {
  1: 'machinegun', // MC
  2: 'handgun',    // Maki
  3: 'machinegun', // Brown
  4: 'rifle',      // Nanjo
  5: 'shotgun',    // Mark
  6: 'rifle',      // Elly
  7: 'handgun',    // Ayase
  8: 'shotgun',    // Yukino
  9: 'rifle',      // Reiji
};

// Equipment ID ranges per type. Keys are the lowercase 4-char ID used in Equipment (PSP).json.
// The ranges follow the sequential ordering in that catalog (verified against the atwiki tables).
const build = (startHex, endHex, suffix) => {
  const out = [];
  const start = parseInt(startHex, 16), end = parseInt(endHex, 16);
  for (let v = start; v <= end; v++) out.push(v.toString(16).padStart(2, '0') + suffix);
  return out;
};
export const weaponIdsByType = {
  sword1h: build('a3', 'ad', '00'),                                   // Scalpel .. Kusanagi's Sword (shared MC & Elly)
  sword1h_mcOnly: ['ae00'],                                           // Spiegel Blade: MC only
  sword2h: ['af00', ...build('b0', 'ba', '00')],                      // Mop (universal) .. Ameno-Murakumo
  spear: build('bb', 'c6', '00'),                                     // Apache Lance .. Ameno-Nuboko
  axe: build('c7', 'd2', '00'),                                       // Two-Handed Axe .. Gokufu Tennou
  whip: build('d3', 'de', '00'),                                      // Gymnast's Rope .. Jingle Whip
  thrown: build('df', 'ea', '00'),                                    // Crane Razor .. Infinity
  bow: build('eb', 'f6', '00'),                                       // Archery Set .. Holy Comet
  fists: [...build('f7', 'ff', '00'), '0001', '0101', '0201'],        // Boxing Glove .. Shinsa Bakenutsu Sho
};
// Scalpel and Mop are documented as "all characters" universal weapons.
const universalMelee = ['a300', 'af00'];
// Empty slot is always allowed.
const emptySlot = '0000';

export const gunIdsByType = {
  handgun: build('03', '0c', '01'),      // Tokarev .. Jolly Roger
  machinegun: build('0d', '1a', '01'),   // Reaper Colt .. Kokonoe Raijinhou
  shotgun: build('1b', '26', '01'),      // Randall Custom .. Megido Fire
  rifle: build('27', '32', '01'),        // M16A2 .. Heaven's Gate
};

// Returns true if the equipment key is legal for the given character ID in the given slot index.
// Slot 2 (ammo), 3 (helmet), 4 (body), 5 (arm), 6 (leg) have no character restriction in the
// base game data we encode here. Weapon (0) and gun (1) do.
export function isEquipmentAllowed(characterId, slotIndex, equipmentKey) {
  const key = String(equipmentKey || '').toLowerCase();
  if (key === emptySlot) return true;
  if (slotIndex === 0) {
    const type = weaponTypeByCharacter[characterId];
    if (!type) return true;
    if (universalMelee.includes(key)) return true;
    if ((weaponIdsByType[type] || []).includes(key)) return true;
    // MC also gets access to the MC-only Spiegel Blade.
    if (characterId === 1 && weaponIdsByType.sword1h_mcOnly.includes(key)) return true;
    return false;
  }
  if (slotIndex === 1) {
    const type = gunTypeByCharacter[characterId];
    if (!type) return true;
    return (gunIdsByType[type] || []).includes(key);
  }
  return true;
}

// Best legal weapon + gun per character, plus universal top-tier ammo and Spiegel armor set.
// Order: [weapon, gun, ammo, helmet, body, arm, leg].
const topAmmo = '3e01';      // Angel Whisper
const topHelmet = '4e01';    // Spiegel Mask
const topBody = '5e01';      // Spiegel Mail
const topArm = '6e01';       // Spiegel Shield
const topLeg = '7e01';       // Spiegel Beine
export const bestEquipmentByCharacter = {
  1: ['ae00', '1a01', topAmmo, topHelmet, topBody, topArm, topLeg], // MC: Spiegel Blade + Kokonoe Raijinhou
  2: ['f600', '0c01', topAmmo, topHelmet, topBody, topArm, topLeg], // Maki: Holy Comet + Jolly Roger
  3: ['c600', '1a01', topAmmo, topHelmet, topBody, topArm, topLeg], // Brown: Ameno-Nuboko + Kokonoe Raijinhou
  4: ['ba00', '3201', topAmmo, topHelmet, topBody, topArm, topLeg], // Nanjo: Ameno-Murakumo + Heaven's Gate
  5: ['d200', '2601', topAmmo, topHelmet, topBody, topArm, topLeg], // Mark: Gokufu Tennou + Megido Fire
  6: ['ad00', '3201', topAmmo, topHelmet, topBody, topArm, topLeg], // Elly: Kusanagi's Sword + Heaven's Gate
  7: ['de00', '0c01', topAmmo, topHelmet, topBody, topArm, topLeg], // Ayase: Jingle Whip + Jolly Roger
  8: ['ea00', '2601', topAmmo, topHelmet, topBody, topArm, topLeg], // Yukino: Infinity + Megido Fire
  9: ['0201', '3201', topAmmo, topHelmet, topBody, topArm, topLeg], // Reiji: Shinsa Bakenutsu Sho + Heaven's Gate
};
