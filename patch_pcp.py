import re

with open('backend/ui/static/js/putCallParity.js', 'r') as f:
    content = f.read()

new_getMonthlyFuture = """        const getMonthlyFuture = (optExpiry, targetTradeDate) => {
            if (!optExpiry) return { date: "-", price: 0.0, vol: 0 };
            const futsForDate = futures[targetTradeDate] || {};
            const futureExpiries = Object.keys(futsForDate).sort((a, b) => new Date(a) - new Date(b));

            const optDate = new Date(optExpiry);
            const optMonth = optDate.getMonth();
            const optYear = optDate.getFullYear();

            // Priority 1: Match exactly the same month and year
            for (let futExp of futureExpiries) {
                const fDate = new Date(futExp);
                if (fDate.getMonth() === optMonth && fDate.getFullYear() === optYear) {
                    return { date: futExp, price: futsForDate[futExp].price, vol: futsForDate[futExp].vol };
                }
            }

            // Priority 2: Fallback to next available future
            for (let futExp of futureExpiries) {
                if (new Date(futExp) >= optDate) {
                    return { date: futExp, price: futsForDate[futExp].price, vol: futsForDate[futExp].vol };
                }
            }
            if (futureExpiries.length > 0) {
                const last = futureExpiries[futureExpiries.length - 1];
                return { date: last, price: futsForDate[last].price, vol: futsForDate[last].vol };
            }
            return { date: "-", price: 0.0, vol: 0 };
        };"""

content = re.sub(
    r"const getMonthlyFuture = \(optExpiry, targetTradeDate\) => \{.*?(?=// Filter and calculate)",
    new_getMonthlyFuture + "\n\n        ",
    content,
    flags=re.DOTALL
)

with open('backend/ui/static/js/putCallParity.js', 'w') as f:
    f.write(content)
