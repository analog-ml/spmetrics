from spmetrics.extractor import SpMetricsExtractor

sim = SpMetricsExtractor(
    "examples/liuLLMbasedAIAgent2025_optimized_g1-5.cir", debug=True
)
sim.run_all_simulations()
print(sim)
