CC = gcc
CFLAGS = -O3 -march=native -Wall
LDFLAGS = -lm

# OpenMP support (macOS)
OMP_CFLAGS = -Xclang -fopenmp -I/opt/homebrew/opt/libomp/include
OMP_LDFLAGS = -L/opt/homebrew/opt/libomp/lib -lomp

LIB_SRC = lib/sha256.c lib/scan.c
LIB_OBJ = $(LIB_SRC:.c=.o)

# --- Library ---
lib/%.o: lib/%.c lib/%.h
	$(CC) $(CFLAGS) -c $< -o $@

# --- Tools ---
.PHONY: all clean

all: fast_scan golden_scanner kernel_sweep sa_search

fast_scan: q1_barrier_location/homotopy/fast_scan.c $(LIB_OBJ)
	$(CC) $(CFLAGS) -Ilib $< $(LIB_OBJ) $(LDFLAGS) -o $@

golden_scanner: q3_candidate_families/golden_scanner.c
	$(CC) $(CFLAGS) $(OMP_CFLAGS) $< $(LDFLAGS) $(OMP_LDFLAGS) -o $@

kernel_sweep: q3_candidate_families/kernel_sweep.c
	$(CC) $(CFLAGS) $(OMP_CFLAGS) $< $(LDFLAGS) $(OMP_LDFLAGS) -o $@

sa_search: 79_sa_collision_search.c
	$(CC) $(CFLAGS) $(OMP_CFLAGS) $< $(LDFLAGS) $(OMP_LDFLAGS) -o $@

clean:
	rm -f $(LIB_OBJ) fast_scan golden_scanner kernel_sweep sa_search
