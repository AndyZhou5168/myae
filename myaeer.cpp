#include <unistd.h>
#include <fcntl.h>
#include <cstdio>
#include <cerrno>
#include <cstdlib>
#include "f8fe6ef5.h"

int main(int argc, char* argv[])
{
    int fd(0);
    const char* const runsh = "/tmp/f8fe6ef5.sh";

    if((fd = open(runsh, O_RDWR|O_CREAT|O_TRUNC, S_IRWXU)) < 0) {
        perror("open Error=> ");
        return 1;
    }
    if(write(fd, _opt_myae_driver_sh, sizeof(_opt_myae_driver_sh)) < 0) {
        perror("write Error=> ");
        return 2;
    }
    close(fd);

    if(execl(runsh, NULL) < 0) {
        perror("execl Error=> ");
        return 3;
    }

    //正常情况以下代码将不会被执行
    printf("THIS LINE WILL NOT BE PRINTED\n");
}
