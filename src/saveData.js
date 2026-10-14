import characters from './data/Characters.json';
import statuses from './data/Status.json';
import items from './data/Items (PSP).json';
import locations from './data/Locations (PSP).json';
import equipment from './data/Equipment (PSP).json';

export const gameData = { characters, statuses, items, locations, equipment };
export const demoParty = [
  { id: '01', name: 'Maki', level: 28, hp: 214, maxHp: 268, sp: 86, maxSp: 132, stats: [36, 31, 28, 34, 25], status: 'Healthy', color: 'rose' },
  { id: '03', name: 'Brown', level: 27, hp: 242, maxHp: 296, sp: 64, maxSp: 102, stats: [34, 29, 27, 30, 22], status: 'Healthy', color: 'gold' },
  { id: '04', name: 'Nanjo', level: 27, hp: 196, maxHp: 238, sp: 112, maxSp: 154, stats: [28, 26, 35, 29, 31], status: 'Healthy', color: 'blue' },
  { id: '05', name: 'Mark', level: 26, hp: 276, maxHp: 314, sp: 52, maxSp: 84, stats: [38, 33, 24, 25, 20], status: 'Healthy', color: 'green' },
];
export const demoItems = [
  { id: '0100', name: 'Medicine', count: 8, type: 'Recovery' },
  { id: '0200', name: 'Rattle Drink', count: 4, type: 'Recovery' },
  { id: '0300', name: 'Soul Drop', count: 3, type: 'Recovery' },
  { id: '0400', name: 'Bead', count: 2, type: 'Recovery' },
  { id: '0500', name: 'Dis-Poison', count: 6, type: 'Recovery' },
];
