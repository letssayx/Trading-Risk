const divRawData = [{
      "symbol": "PFC",
      "company_name": "Power Finance",
      "purpose": "Interim Dividend - Rs 4.50 Per Share",
      "ex_date": "2024-02-19",
      "record_date": "2024-02-20",
      "dividend_type": "Interim",
      "parsed_dividend_amount": 4.5
    }, {
      "symbol": "HDFCBANK",
      "company_name": "HDFC Bank",
      "purpose": "Final Dividend - Rs 19.50 Per Share",
      "ex_date": "2024-05-10",
      "record_date": "2024-05-11",
      "dividend_type": "Final",
      "parsed_dividend_amount": 19.5
}];
const searchFilter = "PFC";
const selectedType = "All";

let filteredActions = divRawData.filter(d => {
    const matchSymbol = !searchFilter ||
        (d.symbol && d.symbol.toUpperCase().includes(searchFilter)) ||
        (d.company_name && d.company_name.toUpperCase().includes(searchFilter));

    let matchType = true;
    if (selectedType !== 'All') {
        const purpose = ((d.subject || '') + ' ' + (d.purpose || '') + ' ' + (d.dividend_type || '') + ' ' + (d.series || '')).toLowerCase();
        if (selectedType === 'Interim' && !purpose.includes('interim')) matchType = false;
        else if (selectedType === 'Final' && !(purpose.includes('dividend') && !purpose.includes('interim') && !purpose.includes('special'))) matchType = false;
        else if (selectedType === 'Special' && !purpose.includes('special')) matchType = false;
        else if (selectedType === 'Bonus' && !purpose.includes('bonus')) matchType = false;
        else if (selectedType === 'Split' && !(purpose.includes('split') || purpose.includes('sub-division'))) matchType = false;
    }

    return matchSymbol && matchType;
});

console.log(filteredActions.length);
