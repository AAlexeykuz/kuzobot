K = 0.18
POWER_K = -1


def calculate_rating(rate, previous_rating, raters_rating):
    k = (raters_rating / previous_rating) ** POWER_K * K
    return (previous_rating + k**2 * rate) / (k**2 + 1)


def calculate_old(rate, previous_rating, raters_rating):
    return (previous_rating**2 + K * rate * raters_rating) / (
        previous_rating + K * raters_rating
    )


rate = 5
previous_rating = 3
raters_rating = 5
print(calculate_rating(rate, previous_rating, raters_rating))
