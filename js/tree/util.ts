import * as fs from "fs";

export function loadJSON(path: string): any {
    return JSON.parse(fs.readFileSync(path, { encoding: 'utf-8' }));
}

export function saveJSON(path: string, data: any): void {
    fs.writeFileSync(path, JSON.stringify(data, null, 2));
}

export function assertNonNull<T>(value: T): T {
    if (value != null) {
        return value;
    }
    throw new Error('Value is null or undefined');
}
