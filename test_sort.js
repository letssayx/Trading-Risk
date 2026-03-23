let arr = ["client_1", "client_10", "client_11", "client_2", "client_3"];
arr.sort((a, b) => {
    let numA = parseInt(a.replace(/[^0-9]/g, ''));
    let numB = parseInt(b.replace(/[^0-9]/g, ''));
    return numA - numB;
});
console.log(arr);
