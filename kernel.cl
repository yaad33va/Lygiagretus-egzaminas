__kernel void process_items(
   __global const int* quantities,
   __global unsigned int* results,
   __global int* indexes,
   __global volatile int* output_count,
   const int count)
{
    int gid = get_global_id(0);
    if (gid >= count)
        return;

    int qty = quantities[gid];
    unsigned int hash = (unsigned int)(qty * 1000 + 100);
    for (int i = 0; i < 10000000; i++) {
        for (int j = 0; j < 40; j++) {
            for(int k = 0; k < 3; k++) {
                 hash = hash * 1103515245u + 12345u;
                 hash ^= (unsigned int)(qty + i+ j+k);
                 hash = (hash >> 16) | (hash << 16);
            }

        }
    }
    if (qty >= 20) {
        int index = atomic_inc(output_count);
        results[index] = hash;
        indexes[index] = gid;
    }
}

__kernel void process_items_single(
   __global const int* quantities,
   __global unsigned int* results,
   __global int* indexes,
   __global volatile int* output_count,
   const int count)
{
    if(get_global_id(0) != 0)
        return;

    for(int gid = 0; gid < count; gid++) {
        int qty = quantities[gid];
        unsigned int hash = (unsigned int)(qty * 1000 + 100);
        for (int i = 0; i < 10000000; i++) {
            for (int j = 0; j < 40; j++) {
                for(int k = 0; k < 3; k++) {
                    hash = hash * 1103515245u + 12345u;
                    hash ^= (unsigned int)(qty + i+ j+k);
                    hash = (hash >> 16) | (hash << 16);
                }
            }
        }
        if (qty >= 20) {
            int index = atomic_inc(output_count);
            results[index] = hash;
            indexes[index] = gid;
        }
    }


}

