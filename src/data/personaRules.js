// Persona 1 persona value caps + recommended loadouts.
// Sources: Megami Tensei Wiki (Persona 1 personas), persona1.wikidot.com,
// aqiu384 Persona 1 fusion calculator, almarsguides Persona 1 guides,
// Ibunroku Megami Isekai Roku skills list, Daihouko arcana affinity table.

// Hard caps enforced on export. Stats/level cap at 99 just like the UI shows;
// rank caps at 8 (fully mastered); SP cost is a single byte; OMP/DMP are u16.
export const personaLimits = {
  level: 99,
  rank: 8,
  stat: 99,
  sp: 255,
  omp: 65535,
  dmp: 65535,
  experience: 9999999,
};

// Best legal persona per playable character, picked by best-affinity arcana
// and endgame strength. Values are the persona IDs used by the save (hex -> dec).
// MC = Vishnu, Maki = Skuld, Brown = Pallas Athena, Nanjo = Shokuin,
// Mark = Shiva, Elly = Vohu Manah, Ayase = Hanuman, Yukino = Kali, Reiji = Lucifer.
export const bestPersonaByCharacter = {
  1: 0x1b, // Vishnu          (Lv86 Emperor)   — MC best affinity
  2: 0x09, // Skuld           (Lv88 Priestess) — Maki best affinity
  3: 0x39, // Pallas Athena   (Lv90 Justice)   — Brown best affinity
  4: 0x5d, // Shokuin         (Lv97 World)     — Nanjo best affinity
  5: 0x2e, // Shiva           (Lv96 Chariot)   — Mark best affinity, has Megidolaon
  6: 0x55, // Vohu Manah      (Lv94 Judgement) — Elly best affinity
  7: 0x02, // Hanuman         (Lv68 Magician)  — Ayase only character with best Magician affinity
  8: 0x13, // Kali            (Lv85 Empress)   — Yukino best affinity
  9: 0x47, // Lucifer         (Lv99 Devil)     — Reiji is the only one who can equip Lucifer well
};

// 14-move "god-tier" loadout: nuke + full healing/revival/status cure + every
// buff/debuff/reflect + Estoma to skip random encounters. Fills every move slot.
export const godTierMoves = [
  0x1e, // Megidolaon         — strongest almighty nuke
  0x64, // Mediarahan         — full-HP heal party
  0x61, // Diarahan           — full-HP heal one ally
  0x6c, // Samarecarm         — revive + full HP
  0x66, // Me Patra           — cure status party
  0x67, // Posumudi           — cure poison
  0x57, // Tarukaja           — attack buff
  0x58, // Rakukaja           — defense buff
  0x59, // Sukukaja           — agility buff
  0x5a, // Makakaja           — magic buff
  0x5b, // Dekaja             — strip enemy buffs
  0x5e, // Tetrakarn          — reflect physical
  0x5d, // Makarakarn         — reflect magic
  0xf3, // Estoma             — avoid random encounters
];

// Top-tier endgame personas to seed the compendium bench with. We skip any that
// are already assigned to a party member in bestPersonaByCharacter so the
// compendium gets maximum variety.
export const compendiumFillers = [
  0x47, // Lucifer       (Lv99 Devil)
  0x2e, // Shiva         (Lv96 Chariot)
  0x5d, // Shokuin       (Lv97 World)
  0x46, // Satan         (Lv95 Judgement)
  0x1b, // Vishnu        (Lv86 Emperor)
  0x55, // Vohu Manah    (Lv94 Judgement)
  0x39, // Pallas Athena (Lv90 Justice)
  0x13, // Kali          (Lv85 Empress)
  0x09, // Skuld         (Lv88 Priestess)
  0x02, // Hanuman       (Lv68 Magician)
  0x4d, // Michael       (Lv93 Judgement / high angel)
  0x3c, // Baal          (Lv84 Emperor)
  0x33, // Odin          (Lv82 Emperor)
  0x32, // Thor          (Lv52 Hierophant)
  0x29, // Armaiti       (strength / lovers endgame)
  0x1f, // Yamaoka       (high Hangedman / Devil bench)
];

// Rough legality check — Reiji is the only character who should receive Lucifer
// (every other playable arcana is Lucifer's worst affinity). Other picks above
// all land on each character's best-affinity row, so we only block the Lucifer
// cross-assignment here. Extend as more constraints are documented.
export function isPersonaAllowedForCharacter(characterId, personaId) {
  if (personaId === 0x47 && characterId !== 9) return false;
  return true;
}
