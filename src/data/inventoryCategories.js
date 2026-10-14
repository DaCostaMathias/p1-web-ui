// Bulk-fill categories for the Inventory tab.
// Each category lists the item IDs (lower-case 4-char hex, same format as the
// JSON catalog keys) and the per-slot target count the "Fill" action should
// top each entry up to. Keep lists in ascending ID order to make them easy to
// cross-check against src/data/Items (PSP).json.
//
// Debug items (0f00, 6600-6800, 6e00-7000), quest/key items (6900-a200),
// and corrupted-equipment slots (7f01-ff01) are intentionally excluded so the
// user never has to clean junk out of their save afterwards.

const range = (startHex, endHex, bank) => {
  const out = [];
  const start = Number.parseInt(startHex, 16);
  const end = Number.parseInt(endHex, 16);
  for (let i = start; i <= end; i++) out.push(i.toString(16).padStart(2, '0') + bank);
  return out;
};

// 0100-0e00 excluding 0f00 Skull Pendulum (debug).
const medicines = range('01', '0e', '00');
// 1000-1c00: Life/Repulse/Core shields + the full incense set + Muscle Drink / Hiranya / Soma.
const statBoosters = range('10', '1c', '00');
// 1d00-2300: Numerous Bell, Divine Voice, Millionaire Bomb, Demon House/Den, Chewing Soul, Metal Card.
const battleItems = range('1d', '23', '00');
// 2400-5500: every elemental spell stone/tablet + cure tablets.
const spellStones = range('24', '55', '00');
// 5600-6500: gems used for persona fusion / shops.
const gems = range('56', '65', '00');

// Weapons live on both banks:
//  - a300-ff00: melee weapons (knives, swords, axes, whips, thrown, bows, gloves)
//  - 0001-0201: three more fist/claw weapons that cross into the 01 bank
const weapons = [...range('a3', 'ff', '00'), ...range('00', '02', '01')];
// 0301-3201: handguns, SMGs, revolvers, shotguns, assault rifles.
const guns = range('03', '32', '01');
// 3301-3e01: gun ammunition (consumable).
const bullets = range('33', '3e', '01');
// 3f01-4e01 helmets, 4f01-5e01 body armor, 5f01-6e01 arm/gauntlet, 6f01-7e01 shoes.
const armor = range('3f', '7e', '01');

export const inventoryCategories = [
  { id: 'medicines',   label: 'Medicines & cures',           target: 88, ids: medicines },
  { id: 'stat',        label: 'Stat boosters & incense',     target: 88, ids: statBoosters },
  { id: 'battle',      label: 'Battle utility items',        target: 88, ids: battleItems },
  { id: 'spellStones', label: 'Spell stones & tablets',      target: 88, ids: spellStones },
  { id: 'gems',        label: 'Gems',                        target: 88, ids: gems },
  { id: 'bullets',     label: 'Bullets & ammunition',        target: 88, ids: bullets },
  { id: 'weapons',     label: 'Weapons (melee, bows, fists)', target: 1,  ids: weapons },
  { id: 'guns',        label: 'Guns',                        target: 1,  ids: guns },
  { id: 'armor',       label: 'Armor (helm, body, arm, leg)', target: 1,  ids: armor },
];

export const inventoryCategoryById = Object.fromEntries(inventoryCategories.map(category => [category.id, category]));
