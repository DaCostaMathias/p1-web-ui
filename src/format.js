import itemsById from './data/Items (PSP).json';
import locations from './data/Locations (PSP).json';
import equipmentById from './data/Equipment (PSP).json';
import personasById from './data/Persona ID.json';
import movesById from './data/Moves.json';
import spellCardsById from './data/Spell Cards.json';
import symbolsByCharacter from './data/Persona Symbol System.json';
import { isEquipmentAllowed, partyLimits } from './data/equipmentRules';
import { personaLimits } from './data/personaRules';
const charactersBySymbol = Object.fromEntries(Object.entries(symbolsByCharacter).map(([character, hex]) => [hex, character]));

const characterNames = { 1: 'MC', 2: 'Maki', 3: 'Brown', 4: 'Nanjo', 5: 'Mark', 6: 'Elly', 7: 'Ayase', 8: 'Yukino', 9: 'Reiji' };
const charactersForFlags = [
  { id: 'ending', label: 'Ending', offset: 5342, values: { Good: 0xa9, Bad: 0xb0 }, aliases:{Good:[0xa9,0xe9],Bad:[0xb0,0x80,0xf1,0x71]} },
  { id: 'nurse', label: 'Saved nurse', offset: 5334, values: { Yes: 0xf0, No: 0x70 }, aliases:{Yes:[0xf0,0xff],No:[0x70,0x00]} },
  { id: 'button', label: 'Button pressed', offset: 5338, values: { Red: 0xdf, Blue: 0x0c }, aliases:{Red:[0xff,0x1f,0xdf,0x0e],Blue:[0x0c,0x00]} },
  { id: 'painting', label: 'Painting liked / weapon lowered', offset: 5340, values: { 'Maki · lowered': 0xf5, 'Chisato · lowered': 0xf4, 'Maki · not lowered': 0xb5, 'Chisato · not lowered': 0xb4 } },
  { id: 'kandori', label: 'Inspired Kandori', offset: 5341, values: { Yes: 0xef, No: 0xe1 }, aliases:{Yes:[0xef,0x27],No:[0xe1,0x21,0x23]} },
  { id: 'forest', label: 'Motivated Maki', offset: 5345, values: { Yes: 0xdf, No: 0xd7 }, aliases:{Yes:[0xdf],No:[0x17,0x57,0xd7]} },
  { id: 'totems', label: 'Totems', offset: 5375, width: 2, values: { None: 0x0000, 'MC': 0x0078, 'MC and Maki': 0x00f9, 'All party members': 0x01f9, 'MC already got one': 0x4078, 'MC and Maki already got theirs': 0x40f9, 'All already got theirs': 0x41f9, 'Other totems already acquired': 0x4079 }, aliases:{'Other totems already acquired':[0x4079,0x407b]} },
];

const little = (bytes, offset, length = 1) => {
  let value = 0;
  for (let i = length - 1; i >= 0; i--) value = value * 256 + (bytes[offset + i] || 0);
  return value;
};
const putLittle = (bytes, offset, length, value) => {
  let n = Number(value) >>> 0;
  for (let i = 0; i < length; i++) { bytes[offset + i] = n & 255; n >>>= 8; }
};
const xorChecksum = bytes => bytes.reduce((checksum, byte) => checksum ^ byte, 0);
const decodeGameText = (bytes, offset, characters = 8) => {
  let result = '';
  for (let i = 0; i < characters; i++) {
    const code = Array.from(bytes.slice(offset + i * 2, offset + i * 2 + 2), value => value.toString(16).padStart(2, '0')).join('');
    if (code === '0000' || code === 'ffff') break;
    result += charactersBySymbol[code] || '?';
  }
  return result;
};
export function detectSave(bytes, filename = '') {
  if (!(bytes instanceof Uint8Array)) throw new TypeError('Save data must be a byte array.');
  const ext = filename.split('.').pop()?.toLowerCase();
  if (bytes.length === 14336) {const validChecksums=bytes[127]===xorChecksum(bytes.subarray(0,127))&&bytes[14335]===xorChecksum(bytes.subarray(128,14335));return { type: ext?.startsWith('c') ? 'PC Suspend' : 'PC', platform: 'PC', editable: true, validChecksums, note:validChecksums?undefined:'PC save checksum mismatch. It can be edited, and export will recalculate the checksums.', size: bytes.length };}
  if (bytes.length === 19336 && little(bytes, 19332, 4) === 0x12345678) return { type: 'PSP unencrypted', platform: 'PSP', editable: true };
  if ([18556, 18572].includes(bytes.length)) return { type: 'PSP Japanese', platform: 'PSP', editable: false, note: 'Japanese PSP saves are not supported by the original editor.' };
  if (bytes.length === 19352) return { type: 'PSP encrypted', platform: 'PSP', editable: false, encrypted: true, note: 'Encrypted Persona 1 PSP save detected. Decrypting locally…' };
  if (ext === 'mcs' && bytes.length >= 14848) {const product=String.fromCharCode(...bytes.subarray(10,22));if(product==='BASLUS-00339')return {type:'PS1 US single save',platform:'PS1',editable:true,ps1:true,ps1Variant:'US'};if(product==='BISLPS-00500')return {type:'PS1 Japanese single save',platform:'PS1',editable:true,ps1:true,ps1Variant:String.fromCharCode(bytes[22])==='C'?'JPCONT':'JP'};}
  const rawHeaders=[
    {variant:'US',signature:'8140826f826482718272826e826d8260814082658268826b826481408194'},
    {variant:'JP',signature:'8f97905f88d995b7985e81408379838b835c8369814082728366815b835e'},
    {variant:'JPCONT',signature:'8f97905f88d995b7985e81408379838b835c8369814082628366815b835e'},
  ];
  if(bytes.length>=14720){const header=Array.from(bytes.subarray(4,34),byte=>byte.toString(16).padStart(2,'0')).join('');const raw=rawHeaders.find(item=>item.signature===header);if(raw)return {type:`PS1 ${raw.variant==='US'?'US':raw.variant==='JP'?'Japanese':'Japanese suspend'} raw save`,platform:'PS1',editable:true,ps1:true,ps1Raw:true,ps1Variant:raw.variant};}
  const memoryCardExtensions=['mcd','gme','mcr','vm1','mci','vgs','vmp'];
  const hasPersonaHeader=(()=>{const signatures=['BASLUS-00339','BISLPS-00500'];for(let i=0;i+12<=bytes.length;i++){if(bytes[i]!==0x42)continue;for(const signature of signatures){let match=true;for(let j=1;j<12;j++)if(bytes[i+j]!==signature.charCodeAt(j)){match=false;break;}if(match)return true;}}return false;})();
  if (bytes.length>=64*1024&&hasPersonaHeader&&(memoryCardExtensions.includes(ext)||bytes.length%128===0)) return { type: 'PS1 memory card image', platform: 'PS1', editable: false, memoryCard:true, note: 'Persona save data was found in this memory card image.' };
  return { type: 'Unknown', platform: 'Unknown', editable: false, note: 'Unsupported size or save signature. Load a raw PC save (.S00–.S06 or .C00–.C06).', size: bytes.length };
}
export function readCore(bytes) {
  if (!(bytes instanceof Uint8Array) || ![14336, 19336].includes(bytes.length)) throw new Error('Expected a supported PC raw save or decrypted PSP save.');
  const b = bytes.slice(0, 14336);
  const party = [];
  for (let slot = 0; slot < 5; slot++) {
    const base = slot * 128, id = b[base + 62];
    if (!id) continue;
    const name = characterNames[id] || `Character ${id}`;
    const nickname=decodeGameText(b,base+64);
    party.push({ slot, id: id.toString(16).padStart(2,'0'), modifier:id, name, nickname, originalNickname:nickname, level: b[base + 106], hp: little(b, base, 2), maxHp: little(b, base + 4, 2), sp: little(b, base + 8, 2), maxSp: little(b, base + 12, 2), stats: Array.from({length:5}, (_,i)=>b[base+107+i]), addedStats:Array.from({length:5},(_,i)=>b[base+112+i]), weaponStats:Array.from({length:4},(_,i)=>little(b,base+46+i*2,2)), personaLevel:b[base+117],personaExperience:little(b,base+28,4),experience:little(b,base+16,4), statusId: b[base+104], status: b[base+104] ? `Status ${b[base+104].toString(16)}` : 'Healthy', equipment: Array.from({length:7},(_,i)=>{const key=Array.from(b.slice(base+32+i*2,base+34+i*2),v=>v.toString(16).padStart(2,'0')).join('');return {key,name:equipmentById[key]||`Equipment ${key}`};}), personas: Array.from({length:3},(_,i)=>b[slot*128+120+i]), color: ['rose','gold','blue','green','purple'][slot] });
  }
  const inventory = [], emptyItemSlots = [];
  for (let i=0;i<387;i++) { const offset=4112+i*2,id=b[offset], encoded=b[offset+1]; if(id) { const key=id.toString(16).padStart(2,'0')+((encoded&1)?'01':'00'); inventory.push({ id:key, name:itemsById[key]||`Item ${key}`, count:Math.floor(encoded/2), type:'Item', slot:i }); } else emptyItemSlots.push(i); }
  const locId = `${b[5236].toString(16).padStart(2,'0')}${b[5237].toString(16).padStart(2,'0')}`;
  const location=Object.values(locations).find(x=>x[0]===locId)?.[1]||'Unknown';
  const locationIndex=Object.entries(locations).find(([key,value])=>value[0]===locId||value[2]===locId)?.[0]||'1';
  const personas = Array.from({length:31},(_,index)=>{const base=664+index*100,id=b[base],owner=b[base+72];return {index,id,name:personasById[id.toString(16).padStart(2,'0')]||`Persona ${id}`,sp:b[base+44],level:b[base+45],stats:Array.from({length:5},(_,i)=>b[base+47+i]),rank:b[base+53],owner,omp:little(b,base-8,2),dmp:little(b,base-6,2),moves:Array.from({length:14},(_,i)=>{const move=b[base+54+i];return {id:move,name:movesById[move.toString(16).padStart(2,'0')]||`Move ${move}`};})};});
  const compendium=Array.from(b.slice(3848,3864));
  const spellCards = Array.from({length:12},(_,index)=>{const id=b[5136+index];return {slot:index,id,name:spellCardsById[id.toString(16).padStart(2,'0')]||`Spell card ${id}`};});
  const storyFlags = charactersForFlags.map(flag=>{const value=little(b,flag.offset,flag.width||1);return {...flag,value,originalValue:value,selected:Object.entries(flag.values).find(([label,allowed])=>(flag.aliases?.[label]||[allowed]).includes(value))?.[0]||'Unknown'};});
  const tranquilityValue=[0x0f,0xdf,0xff,0x0c,0x1f,0x0e].includes(b[5338])?2:b[5334]>=48||b[5338]>=128?1:0;
  storyFlags.unshift({id:'tranquility',label:'Tranquility',values:{Tranquil:0,Apocalypse:1,Ideal:2},value:tranquilityValue,originalValue:tranquilityValue,selected:['Tranquil','Apocalypse','Ideal'][tranquilityValue]});
  const locationType=little(b,5232,2),mapCode=little(b,5236,2);
  const hexWord=offset=>Array.from(b.subarray(offset,offset+2),value=>value.toString(16).padStart(2,'0')).join('').toUpperCase();
  const seconds=bytes.length===14336?0:little(bytes,17692,4);
  return { party, inventory, emptyItemSlots, personas, compendium, spellCards, storyFlags, money:little(b,4104,4), coins:little(b,4108,4), seconds, difficulty:b[17560]||0, locationId:locId, locationIndex, locationType, mapLocation:mapCode<=2?mapCode:3, mapWard:little(b,5240,2), locationHex:hexWord(5236), warpHex:hexWord(5300), floorHex:hexWord(5302), xHex:hexWord(5304), yHex:hexWord(5306), directionHex:hexWord(5308), location, saveTag:decodeGameText(b,5192), firstName:decodeGameText(b,5168), lastName:decodeGameText(b,5152) };
}
export function extractPs1Core(bytes) {
  if (!(bytes instanceof Uint8Array) || bytes.length < 14720) throw new Error('PS1 save is too short to contain the Persona save payload.');
  const rawHeaders=[
    {variant:'US',signature:'8140826f826482718272826e826d8260814082658268826b826481408194'},
    {variant:'JP',signature:'8f97905f88d995b7985e81408379838b835c8369814082728366815b835e'},
    {variant:'JPCONT',signature:'8f97905f88d995b7985e81408379838b835c8369814082628366815b835e'},
  ];
  const rawPrefix=Array.from(bytes.subarray(4,34),byte=>byte.toString(16).padStart(2,'0')).join('');
  if(rawHeaders.some(item=>rawPrefix.startsWith(item.signature))){if(bytes.length<14720)throw new Error('PS1 raw save is too short to contain the Persona payload.');return bytes.slice(384,14720);}
  if(bytes.length<14848)throw new Error('PS1 single save is too short to contain the Persona payload.');
  const product=String.fromCharCode(...bytes.subarray(10,22));
  if (!['BASLUS-00339','BISLPS-00500'].includes(product)) throw new Error('Unrecognized Persona 1 PS1 single-save header.');
  return bytes.slice(512,512+14336);
}
export function extractPs1MemoryCard(bytes) {
  if (!(bytes instanceof Uint8Array) || bytes.length<64*1024) throw new Error('The PS1 memory-card image is too small.');
  const products=[],tags=[];
  const productIds=[['BASLUS-00339','US'],['BISLPS-00500','JP']];
  const tagSignatures=[
    {variant:'US',bytes:[0x82,0x6f,0x82,0x64,0x82,0x71,0x82,0x72,0x82,0x6e,0x82,0x6d,0x82,0x60],prefixBytes:6},
    {variant:'JP',bytes:[0x8f,0x97,0x90,0x5f,0x88,0xd9,0x95,0xb7,0x98,0x5e,0x81,0x40,0x83,0x79,0x83,0x8b,0x83,0x5c,0x83,0x69],prefixBytes:4},
  ];
  for(let i=0;i+12<=bytes.length;i++){
    for(const [id,variant] of productIds){let match=true;for(let j=0;j<id.length;j++)if(bytes[i+j]!==id.charCodeAt(j)){match=false;break;}if(match&&i>=10)products.push({headerStart:i-10,variant});}
    for(const signature of tagSignatures){let match=true;for(let j=0;j<signature.bytes.length;j++)if(bytes[i+j]!==signature.bytes[j]){match=false;break;}if(match)tags.push({bodyStart:i-signature.prefixBytes,variant:signature.variant});}
  }
  const saves=[];
  for(let index=0;index<Math.min(products.length,tags.length);index++){
    const product=products[index],tag=tags[index],headerStart=product.headerStart,bodyStart=tag.bodyStart;
    if(product.variant!==tag.variant||headerStart<0||headerStart+128>bytes.length||bodyStart<0||bodyStart+16384>bytes.length)continue;
    const output=new Uint8Array(16512);output.set(bytes.subarray(headerStart,headerStart+128));output.set(bytes.subarray(bodyStart,bodyStart+16384),128);
    if(!['BASLUS-00339','BISLPS-00500'].includes(String.fromCharCode(...output.subarray(10,22))))continue;
    const variant=product.variant==='JP'&&output[22]===0x43?'JPCONT':product.variant;
    saves.push({bytes:output,variant,label:`${variant==='US'?'US':variant==='JPCONT'?'Japanese suspend':'Japanese'} PS1 save ${saves.length+1}`});
  }
  if(!saves.length)throw new Error('No supported Persona 1 save entries could be extracted from this memory-card image.');
  return saves;
}
export async function createPs1Save(core, variant='US', slot=0) {
  if (!(core instanceof Uint8Array) || core.length !== 14336) throw new Error('PS1 export requires a 14,336-byte save payload.');
  if (!['US','JP','JPCONT'].includes(variant)) throw new Error('Choose a supported PS1 save type.');
  if (!Number.isInteger(Number(slot)) || Number(slot)<0 || Number(slot)>6) throw new Error('PS1 save slot must be from 0 to 6.');
  const templates={US:'PS1USInput.bin',JP:'PS1JPInput.bin',JPCONT:'PS1JPCONTInput.bin'};
  const response=await fetch(`${import.meta.env.BASE_URL}${templates[variant]}`);
  if (!response.ok) throw new Error('Could not load the bundled PS1 save template.');
  const template=new Uint8Array(await response.arrayBuffer());
  if(template.length!==2176)throw new Error('The bundled PS1 save template has an unexpected size.');
  const output=new Uint8Array(template.length+core.length);
  output.set(template.subarray(0,512));output.set(core,512);output.set(template.subarray(512),512+core.length);
  output[22]=variant==='JPCONT'?0x43:0x53;output[23]=0x30+Number(slot);
  output[127]=xorChecksum(output.subarray(0,127));
  return output;
}
export function writeEdits(original, edited) {
  if (!(original instanceof Uint8Array) || ![14336,19336].includes(original.length)) throw new Error('Unsupported save length.');
  const bounded = (value,min,max,label) => { const n=Number(value); if (!Number.isInteger(n)||n<min||n>max) throw new Error(`${label} must be between ${min} and ${max}.`); return n; };
  const b = original.slice();
  putLittle(b,4104,4,bounded(edited.money,0,999999999,'Money')); putLittle(b,4108,4,bounded(edited.coins,0,999999999,'Coins'));
  const playSeconds=bounded(edited.seconds,0,0xffffffff,'Play time');
  if(original.length===19336)putLittle(b,17692,4,playSeconds);
  const writeName=(offset,value,label)=>{if(value===undefined||value===decodeGameText(original,offset))return;const chars=Array.from(String(value).trim());if(chars.length>8)throw new Error(`${label} must be 8 characters or fewer.`);for(let j=0;j<8;j++){const character=chars[j]??' ',code=symbolsByCharacter[character];if(code===undefined)throw new Error(`${label} contains an unsupported symbol: ${character}`);const number=Number.parseInt(code,16);b[offset+j*2]=number>>8;b[offset+j*2+1]=number&255;}};
  writeName(5168,edited.firstName,'First name');writeName(5152,edited.lastName,'Last name');
  const difficulty=bounded(edited.difficulty,0,2,'Difficulty');if(b.length>17560)b[17560]=difficulty;
  edited.party.forEach((p,index)=>{
    const slot=bounded(p.slot??index,0,4,'Party slot'), i=slot*128;
    const characterId=bounded(p.modifier??Number.parseInt(p.id,16),1,9,'Character modifier');
    putLittle(b,i,2,bounded(p.hp,0,partyLimits.hp,'HP'));
    putLittle(b,i+4,2,bounded(p.maxHp,0,partyLimits.hp,'Max HP'));
    putLittle(b,i+8,2,bounded(p.sp,0,partyLimits.sp,'SP'));
    putLittle(b,i+12,2,bounded(p.maxSp,0,partyLimits.sp,'Max SP'));
    b[i+62]=characterId;
    b[i+104]=bounded(p.statusId??b[i+104],0,255,'Status');
    b[i+106]=bounded(p.level,0,partyLimits.level,'Level');
    p.stats.forEach((n,j)=>b[i+107+j]=bounded(n,0,partyLimits.stat,'Stat'));
    (p.addedStats||[]).forEach((n,j)=>b[i+112+j]=bounded(n,0,partyLimits.addedStat,'Added stat'));
    (p.weaponStats||[]).forEach((n,j)=>putLittle(b,i+46+j*2,2,bounded(n,0,999,'Weapon stat')));
    b[i+117]=bounded(p.personaLevel??b[i+117],0,partyLimits.personaLevel,'Persona level');
    putLittle(b,i+28,4,bounded(p.personaExperience??little(b,i+28,4),0,partyLimits.personaExperience,'Persona EXP'));
    putLittle(b,i+16,4,bounded(p.experience??little(b,i+16,4),0,partyLimits.experience,'Character EXP'));
    (p.personas||[]).forEach((persona,j)=>b[i+120+j]=bounded(persona,0,255,'Equipped persona'));
    if(p.nickname!==undefined&&p.nickname!==p.originalNickname){const name=Array.from(p.nickname);if(name.length>8)throw new Error('Character nicknames must be 8 characters or fewer.');for(let j=0;j<8;j++){const hex=j<name.length?symbolsByCharacter[name[j]]:null;if(j<name.length&&!hex)throw new Error(`Character nickname contains an unsupported symbol: ${name[j]}`);const value=hex?Number.parseInt(hex,16):0;b[i+64+j*2]=(value>>8)&255;b[i+65+j*2]=value&255;}}
    (p.equipment||[]).forEach((item,j)=>{
      const id=Number.parseInt(item.key,16);
      if(!Number.isInteger(id)||id<0||id>65535)return;
      // Enforce character-appropriate weapons and guns (slots 0 and 1).
      if((j===0||j===1)&&!isEquipmentAllowed(characterId,j,item.key)){
        const kind=j===0?'weapon':'gun';
        throw new Error(`${p.name||`Character ${characterId}`} cannot equip ${item.name||item.key} in the ${kind} slot. Choose a compatible item.`);
      }
      b[i+32+j*2]=(id>>8)&255;b[i+33+j*2]=id&255;
    });
  });
  edited.inventory.forEach((item)=>{ if(item.slot == null)return; const slot=bounded(item.slot,0,386,'Item slot'),count=bounded(item.count,0,99,'Item quantity'),key=Number.parseInt(item.id,16); if(!Number.isInteger(key)||key<0||key>65535)throw new Error('Invalid item ID.'); const i=4112+slot*2; if(count===0){b[i]=0;b[i+1]=0;}else{b[i]=(key>>8)&255;b[i+1]=(count*2)|(key&1);} });
  (edited.personas||[]).forEach(p=>{const i=664+bounded(p.index,0,30,'Persona slot')*100;b[i]=bounded(p.id,0,255,'Persona ID');b[i+44]=bounded(p.sp,0,personaLimits.sp,'Persona SP cost');b[i+45]=bounded(p.level,0,personaLimits.level,'Persona level');p.stats.forEach((n,j)=>b[i+47+j]=bounded(n,0,personaLimits.stat,'Persona stat'));b[i+53]=bounded(p.rank,0,personaLimits.rank,'Persona rank');b[i+72]=bounded(p.owner,0,255,'Persona owner');putLittle(b,i-8,2,bounded(p.omp,0,personaLimits.omp,'OMP'));putLittle(b,i-6,2,bounded(p.dmp,0,personaLimits.dmp,'DMP'));(p.moves||[]).forEach((move,j)=>b[i+54+j]=bounded(move.id,0,255,'Move ID'));});
  (edited.spellCards||[]).forEach(card=>{const slot=bounded(card.slot,0,11,'Spell card slot');b[5136+slot]=bounded(card.id,0,255,'Spell card ID');});
  (edited.compendium||[]).forEach((persona,index)=>{b[3848+bounded(index,0,15,'Compendium slot')]=bounded(persona,0,255,'Compendium persona');});
  const editedFlags=edited.storyFlags||[],tranquility=editedFlags.find(flag=>flag.id==='tranquility'),nurseFlag=editedFlags.find(flag=>flag.id==='nurse'),buttonFlag=editedFlags.find(flag=>flag.id==='button');
  const tranquilityChanged=tranquility&&tranquility.value!==tranquility.originalValue;
  if(tranquilityChanged){
    const choices={0:[0x00,0x00,0x00],1:[0xf0,0xf0,0x00],2:[0xf0,0xf0,0xdf]},[nurseByte,secondByte,buttonByte]=choices[bounded(tranquility.value,0,2,'Tranquility')];
    if(nurseFlag&&nurseFlag.value!==nurseFlag.originalValue&&bounded(nurseFlag.value,0,255,'Saved nurse')!==nurseByte)throw new Error('Tranquility and saved-nurse edits overlap. Choose one of those changes at a time.');
    if(buttonFlag&&buttonFlag.value!==buttonFlag.originalValue&&bounded(buttonFlag.value,0,255,'Button pressed')!==buttonByte)throw new Error('Tranquility and button edits overlap. Choose one of those changes at a time.');
  }
  editedFlags.forEach(flag=>{const spec=charactersForFlags.find(item=>item.id===flag.id);if(!spec||flag.id==='tranquility')return;putLittle(b,spec.offset,spec.width||1,bounded(flag.value,0,spec.width?65535:255,'Story flag'));});
  if(tranquilityChanged){const choices={0:[0x00,0x00,0x00],1:[0xf0,0xf0,0x00],2:[0xf0,0xf0,0xdf]},[nurseByte,secondByte,buttonByte]=choices[tranquility.value];b[5334]=nurseByte;b[5336]=secondByte;b[5338]=buttonByte;}
  const locationMode=bounded(edited.locationType??little(b,5232,2),0,3,'Location mode');
  if(![0,2,3].includes(locationMode))throw new Error('Choose a supported location mode.');
  putLittle(b,5232,2,locationMode);
  if(locationMode===2&&edited.mapLocation!==undefined){const map=bounded(edited.mapLocation,0,4,'2D map');if(map<3)putLittle(b,5236,2,map);else if(map===3)putLittle(b,5240,2,bounded(edited.mapWard??little(b,5240,2),0,5,'Ward'));else b.fill(0,5242,5264);}
  if(locationMode!==2&&edited.locationEditMode==='advanced'){
    const fields=[[edited.locationHex,5236,'Location'],[edited.warpHex,5300,'Warp'],[edited.floorHex,5302,'Floor'],[edited.xHex,5304,'X position'],[edited.yHex,5306,'Y position'],[edited.directionHex,5308,'Direction']];
    for(const [value,offset,label] of fields){if(!/^[\da-f]{4}$/i.test(String(value??'')))throw new Error(`${label} must be exactly four hexadecimal digits.`);b[offset]=Number.parseInt(value.slice(0,2),16);b[offset+1]=Number.parseInt(value.slice(2,4),16);}
    b[5240]=b[5302];b[5241]=b[5303];b[5244]=b[5304];b[5245]=b[5305];b[5248]=b[5306];b[5249]=b[5307];b[5252]=b[5308];b[5253]=b[5309];b[5228]=0;b[5229]=0;
  }else if(locationMode!==2&&edited.locationIndex!==undefined){const entry=locations[String(edited.locationIndex)];if(!entry)throw new Error('Select a valid location.');const locationId=locationMode===0?entry[2]:entry[0];for(let j=0;j<2;j++){b[5236+j]=Number.parseInt(locationId.slice(j*2,j*2+2),16);b[5300+j]=Number.parseInt(entry[2].slice(j*2,j*2+2),16);b[5302+j]=Number.parseInt(entry[3].slice(j*2,j*2+2),16);b[5240+j]=Number.parseInt(entry[3].slice(j*2,j*2+2),16);b[5304+j]=Number.parseInt(entry[4].slice(j*2,j*2+2),16);b[5244+j]=Number.parseInt(entry[4].slice(j*2,j*2+2),16);b[5306+j]=Number.parseInt(entry[5].slice(j*2,j*2+2),16);b[5248+j]=Number.parseInt(entry[5].slice(j*2,j*2+2),16);b[5308+j]=Number.parseInt(entry[6].slice(j*2,j*2+2),16);b[5252+j]=Number.parseInt(entry[6].slice(j*2,j*2+2),16);}b[5228]=0;b[5229]=0;}
  if (typeof edited.saveTag === 'string' && edited.saveTag!==decodeGameText(original,5192)) { const tag=Array.from(edited.saveTag);if(tag.length>8)throw new Error('Save tags must be 8 characters or fewer.');b.fill(0,5192,5208);tag.forEach((character,index)=>{const hex=symbolsByCharacter[character];if(!hex)throw new Error(`Save tag contains an unsupported symbol: ${character}`);const value=Number.parseInt(hex,16);b[5192+index*2]=(value>>8)&255;b[5193+index*2]=value&255;}); }
  // PC raw saves use an XOR checksum; the PSP container maintains its hashes during encryption.
  if (original.length === 14336) {
    b[127]=xorChecksum(b.subarray(0,127));
    b[14335]=xorChecksum(b.subarray(128,14335));
  }
  return b;
}

