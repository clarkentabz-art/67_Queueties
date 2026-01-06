# selection_sort.py

def selection_sort(array):
    n = len(array)
    steps = []  # store swaps for animation

    for step in range(n):
        min_index = step
        for i in range(step + 1, n):
            if array[i] < array[min_index]:
                min_index = i

        if min_index != step:
            array[step], array[min_index] = array[min_index], array[step]
            steps.append((step, min_index))  # record swap

    return array, steps
