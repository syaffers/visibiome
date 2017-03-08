
include Makefile.conf
include Makefile.inc

FCFLAGS=$(COORD_UTIL_FCFLAGS)
FC=${COORD_UTIL_FC} $(FCFLAGS)

F2PY=f2py --fcompiler=$(F2PY_FC_NAME) --f90flags="$(FCFLAGS)" --arch="$(FC_ARCH_FLAGS)" --link-lapack_opt # -DF2PY_REPORT_ON_ARRAY_COPY

all: coord_math.o coord_math_f.so

clean:
	rm -f *.o *.so *.mod 

%.o: %.f90
	${FC} -c $< -o $@

coord_math_f.so: coord_math.f90
	$(F2PY) -c -m coord_math_f coord_math.f90

coord_math.o: coord_math.f90
	${FC} -c $< -o $@

coord_math: coord_math.o

