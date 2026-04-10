CC = gcc

ifeq ($(shell uname),Darwin)
  STACK_FLAGS = -fno-stack-protector
else
  STACK_FLAGS = -fno-stack-protector -z execstack
endif

CFLAGS = ${STACK_FLAGS} -Wall -Iutil -Iatm -Ibank -Irouter -I.

all: bin bin/atm bin/bank bin/router bin/init

bin:
	mkdir -p bin

bin/atm : atm/atm-main.c atm/atm.c
	${CC} ${CFLAGS} atm/atm.c atm/atm-main.c -o bin/atm

bin/bank : bank/bank-main.c bank/bank.c util/hash_table.c util/list.c
	${CC} ${CFLAGS} bank/bank.c bank/bank-main.c util/hash_table.c util/list.c -o bin/bank

bin/router : router/router-main.c router/router.c
	${CC} ${CFLAGS} router/router.c router/router-main.c -o bin/router

bin/init : init.c
	${CC} ${CFLAGS} init.c -o bin/init

clean:
	cd bin && rm -f *
