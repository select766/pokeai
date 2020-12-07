import * as fs from "fs";

export function loadJSON(path: string): any {
    return JSON.parse(fs.readFileSync(path, { encoding: 'utf-8' }));
}

export function saveJSON(path: string, data: any): void {
    fs.writeFileSync(path, JSON.stringify(data, null, 2));
}
