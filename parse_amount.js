const testCases = [
  "To consider and approve the financial results for the period ended March 31, 2026 and dividend, if any.",
  "Dividend of Rs. 54 per share",
  "Interim Dividend of Rs 5.50/- per share",
  "Recommendation of final dividend of Rs. 50/- per equity share",
  "Declaration of Interim Dividend of 54/- per share",
  "Dividend - Rs 54"
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
