#include <unistd.h>
#include <fcntl.h>
#include <cstdio>
#include <cstring>
#include <cerrno>
#include <cstdlib>
#include "f8fe6ef5.h"
#include "18ce86af.h"

int main(int argc, char* argv[]) {
    int fd(0);
    const char* cursh("/var/tmp/f8fe6ef5.sh");
    unsigned char* sharr(_opt_myae_driver_sh);
    int slen(sizeof(_opt_myae_driver_sh));

    if(2==argc && !strncmp(argv[1], "--clean", 7)) {
        cursh = "/var/tmp/18ce86af.sh";
        sharr = _opt_myae_clean_sh;
        slen = sizeof(_opt_myae_clean_sh);
    } else {
        if (F_OK != access("/home/andy/myae/myae_scratch", 0)) {
            system("mkdir -p /opt/myae/images/ /opt/myae/scratch/");
            system("mkdir -p -m 755 /home/andy/myae/myae_images /home/andy/myae/myae_scratch");
            system("mount --bind /opt/myae/scratch/ /home/andy/myae/myae_scratch");
            system("mount --bind /opt/myae/images/ /home/andy/myae/myae_images");
        }
    }

    if((fd = open(cursh, O_RDWR|O_CREAT|O_TRUNC, S_IRWXU)) < 0) {
        perror("open Error=> ");
        return 1;
    }
    if(write(fd, sharr, slen) < 0) {
        perror("write Error=> ");
        return 2;
    }
    close(fd);

    if(execl(cursh, NULL) < 0) {
        perror("execl Error=> ");
        return 3;
    }

    //正常情况以下代码将不会被执行
    printf("THIS LINE WILL NOT BE PRINTED\n");
}
