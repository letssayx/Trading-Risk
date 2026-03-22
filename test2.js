const d = {
      "symbol": "PFC",
      "company_name": "Power Finance",
      "purpose": "Interim Dividend - Rs 4.50 Per Share",
      "ex_date": "2024-02-19",
      "record_date": "2024-02-20",
      "dividend_type": "Interim",
      "parsed_dividend_amount": 4.5
};
const searchFilter = "PFC";

const matchSymbol = !searchFilter ||
    (d.symbol && d.symbol.toUpperCase().includes(searchFilter)) ||
    (d.company_name && d.company_name.toUpperCase().includes(searchFilter));

console.log(matchSymbol);
