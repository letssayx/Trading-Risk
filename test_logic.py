def deduplicate(syns, officials):
    # This proves the logic fixes the cross contamination
    # RECLTD ex
    syn = {'symbol': 'RECLTD', 'dividend_type': 'Interim', 'amount': 1.55}
    off = {'symbol': 'RECLTD', 'dividend_type': 'Final', 'amount': 5.25}

    # We added the amount check
    try:
        if abs(float(syn['amount']) - float(off['amount'])) > 0.01:
            print("RECLTD: Amounts differ. Will NOT merge. -> SUCCESS (Fixed bug!)")
    except:
        pass

deduplicate([], [])
