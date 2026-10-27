/* Loss-detecting native case input. JSON strings remain data. */
(()=>{
  function decimalIdentity(raw) {
    let [mantissa, exponent = "0"] = raw.toLowerCase().split("e");
    const negative = mantissa.startsWith("-");
    if (negative) mantissa = mantissa.slice(1);
    const [whole, fraction = ""] = mantissa.split(".");
    let digits = (whole + fraction).replace(/^0+/, "");
    if (!digits) return "0";
    let scale = BigInt(exponent) - BigInt(fraction.length);
    const trailing = digits.match(/0+$/)?.[0].length || 0;
    if (trailing) { digits = digits.slice(0, -trailing); scale += BigInt(trailing); }
    return (negative ? "-" : "") + digits + "e" + scale;
  }
  function parse(text) {
    if (typeof text !== "string") throw Error("Expected JSON text.");
    if (new TextEncoder().encode(text).length > 32 * 1024 * 1024) throw Error("JSON exceeds 32 MiB; use a smaller source edition.");
    if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
    let pos = 0;
    const fail = message => { throw Error(`${message} at JSON character ${pos + 1}.`); };
    const space = () => { while (/[\x20\t\r\n]/.test(text[pos] || "\0")) pos++; };
    function string() {
      const start = pos++;
      while (pos < text.length) {
        const c = text[pos++];
        if (c === "\\") { pos++; continue; }
        if (c === '"') {
          try { return JSON.parse(text.slice(start, pos)); }
          catch (_) { fail("Invalid JSON string"); }
        }
      }
      fail("Unterminated JSON string");
    }
    function value(depth) {
      if (depth > 64) fail("JSON nesting exceeds 64 levels");
      space();
      const c = text[pos];
      if (c === '"') return string();
      if (c === "{") {
        pos++; space();
        const result = {}, seen = new Set();
        if (text[pos] === "}") { pos++; return result; }
        while (true) {
          space(); if (text[pos] !== '"') fail("Expected an object key");
          const key = string();
          if (seen.has(key)) fail(`Duplicate JSON key ${JSON.stringify(key)}`);
          seen.add(key); space(); if (text[pos++] !== ":") fail("Expected a colon");
          Object.defineProperty(result, key, {value:value(depth + 1), enumerable:true, writable:true, configurable:true});
          space(); const next = text[pos++];
          if (next === "}") return result;
          if (next !== ",") fail("Expected a comma or closing brace");
        }
      }
      if (c === "[") {
        pos++; space(); const result = [];
        if (text[pos] === "]") { pos++; return result; }
        while (true) {
          result.push(value(depth + 1)); space(); const next = text[pos++];
          if (next === "]") return result;
          if (next !== ",") fail("Expected a comma or closing bracket");
        }
      }
      for (const [literal, result] of [["true",true],["false",false],["null",null]]) {
        if (text.startsWith(literal, pos)) { pos += literal.length; return result; }
      }
      const token = text.slice(pos).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/)?.[0];
      if (!token) fail("Expected a JSON value");
      if (token.length > 512) fail("Numeric token is too long for this browser editor");
      const number = Number(token);
      if (!Number.isFinite(number) || (Number.isInteger(number) && !Number.isSafeInteger(number)) || decimalIdentity(token) !== decimalIdentity(String(number))) {
        fail("Number cannot round-trip exactly through this browser editor; keep exact identifiers in quoted strings or use the native workflow");
      }
      pos += token.length; return number;
    }
    const result = value(0); space(); if (pos !== text.length) fail("Unexpected trailing JSON content");
    return result;
  }
window.CaseJSON={parse};
})();
