import cProfile
import pstats

cProfile.run("import slidingpuzzle", filename="profile.info")

stats = pstats.Stats("profile.info")
stats.strip_dirs()
stats.sort_stats('tottime')
stats.print_stats(.1, 'solver')
stats.print_callees('move')
stats.print_callees('clone')
