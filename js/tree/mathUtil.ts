export function rnorm() {
    return Math.sqrt(-2 * Math.log(1 - Math.random())) * Math.cos(2 * Math.PI * Math.random());
}

export function argsort(ary: number[]): number[] {
    const idxs = ary.map((v, i) => [v, i]);
    idxs.sort((a, b) => a[0] - b[0]);
    return idxs.map((a) => a[1]);
}
