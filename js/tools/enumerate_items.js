/*
持たせられる道具を列挙
node ./js/tools/enumerate_items.js > data/dataset/all_items.json
*/

const items = require('../../Pokemon-Showdown/data/items').BattleItems;

const item_ids = [];
for (const key in items) {
    if (items.hasOwnProperty(key)) {
        const element = items[key];
        if (element.gen === 2 && !element.isPokeball) {
            item_ids.push(key);
        }
    }
}
process.stdout.write(JSON.stringify(item_ids, null, 2));
