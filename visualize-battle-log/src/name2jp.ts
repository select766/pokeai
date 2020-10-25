
let dataset: {[key: string]: string} = {};
(async () => {
  const f = await fetch('/name2jp.json');
  dataset = (await f.json())['name2jp'];
})();

export function name2jp(name: string): string {
  return dataset[name] || name;
}
