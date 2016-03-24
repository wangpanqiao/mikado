import cython


@cython.profile(True)
@cython.cdivision(True)
cpdef double calc_f1(double recall, double precision):
    """
    Static method to calculate the F1 statistic given precision
    and recall (order is unimportant). Definition:
    F1 = (2 * precision * recall) / (precision + recall)
    """
    cdef double result, summa, product

    if max(precision, recall) == 0:
        return 0
    else:
        product = 2 * precision * recall
        summa = precision + recall
        result = product / summa
        return result
