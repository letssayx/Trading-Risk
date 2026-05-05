const testCases = [
  "Dividend - 54"
];

for (let purpose of testCases) {
    let amountMatch = purpose.match(/(?:rs\.?|rupees?)\s*([0-9]+(?:\.[0-9]+)?)/i) ||
                      purpose.match(/([0-9]+(?:\.[0-9]+)?)\s*\/\-/i) ||
                      purpose.match(/dividend\s+of\s+([0-9]+(?:\.[0-9]+)?)/i) ||
                      purpose.match(/dividend.*?\s+([0-9]+(?:\.[0-9]+)?)\s+per/i);
    console.log(`Purpose: "${purpose}"`);
    if (amountMatch) {
        console.log(`Matched Amount: ${amountMatch[1]}`);
    } else {
        console.log(`Matched Amount: null`);
    }
    console.log("---");
}
