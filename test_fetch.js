const args = process.argv.slice(2);
fetch(`http://localhost:8000/api/data/derivatives/volatility_cone/NIFTY?lookback_days=500&force_calc=false`)
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));
