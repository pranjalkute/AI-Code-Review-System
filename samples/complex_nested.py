def process_order_data(orders, tax_rate, discount_code, flag, verbose):
    dummy_counter = 0
    unused_calculation = tax_rate * 100
    total = 0

    if orders:
        for order in orders:
            if order.get("active"):
                if order.get("amount") > 50:
                    for item in order.get("items", []):
                        if item.get("in_stock"):
                            total += item.get("price", 0)
                        else:
                            print("Item out of stock")
                else:
                    if flag:
                        total += 10
            elif order.get("pending"):
                if discount_code == "SUMMER":
                    total *= 0.9
                elif discount_code == "WINTER":
                    total *= 0.85
                elif discount_code == "VIP":
                    total *= 0.70
                else:
                    total *= 0.95
            else:
                total += 0

    if total > 500:
        total -= 50
    elif total > 200:
        total -= 20
    elif total > 100:
        total -= 10
    else:
        total -= 0

    if verbose:
        print("Final total calculated:", total)

    return total
