let purpose = "dividend of 54/- per share";
let amountMatch = purpose.match(/(?:rs\\.?|rupees?)\s*([0-9]+(?:\\.[0-9]+)?)/i) || purpose.match(/([0-9]+(?:\.[0-9]+)?)\s*\/\-/i) || purpose.match(/dividend\s+of\s+([0-9]+(?:\.[0-9]+)?)/i) || purpose.match(/dividend.*?\s+([0-9]+(?:\.[0-9]+)?)\s+per/i);
if (amountMatch) {
    console.log(amountMatch[1]);
}
