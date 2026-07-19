import timeit
from agentik_dongu import gorev_tipini_belirle

def run_benchmark():
    test_cases = [
        "Bana bir web sitesi yap, url'si http://example.com olsun",
        "excel dosyasini ac, kopyala",
        "Bu grafikleri analiz et, bana bir istatistik tablosu cikar",
        "python script yaz bana",
        "Twitter trendlerini sosyal medya analizi yap",
        "Naber kanka nasilsin",
    ]

    # We will test running it 10,000 times for each query to get a good measurement

    def test_func():
        for case in test_cases:
            gorev_tipini_belirle(case)

    # Number of iterations
    n = 100000

    time_taken = timeit.timeit(test_func, number=n)

    print(f"Benchmark for gorev_tipini_belirle")
    print(f"Iterations: {n}")
    print(f"Total time taken: {time_taken:.5f} seconds")
    print(f"Time per function call: {time_taken / (n * len(test_cases)) * 1000000:.2f} microseconds")

if __name__ == "__main__":
    run_benchmark()