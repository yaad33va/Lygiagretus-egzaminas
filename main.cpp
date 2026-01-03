/*
Vienas workeris - data1.json
Python program completed in 136.47 seconds
OpenCL thread completed in 2054014 ms


 */
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <thread>
#include <mutex>
#include <chrono>
#include <sstream>
#include <iomanip>
#include <json.hpp>


#ifdef __APPLE__
#include <OpenCL/opencl.h>
#else
#include <CL/cl.h>
#endif

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#endif

using json = nlohmann::json;

struct FoodItem {
    std::string name;
    int quantity{};
    double price{};
    unsigned int opencl_result{};
    double python_result{};
};

std::vector<FoodItem> parseJSON(const std::string& filename) {
    std::vector<FoodItem> items;
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << filename << std::endl;
        return items;
    }

    json j;
    file >> j;
    for (const auto& item : j["foods"]) {
        FoodItem food_item;
        food_item.name = item["name"].get<std::string>();
        food_item.quantity = item["quantity"].get<int>();
        food_item.price = item["price"].get<double>();
        items.push_back(food_item);
    }

    return items;
}

// OpenCL thread function
void openclThread(const std::vector<FoodItem>& items,
    std::vector<FoodItem>& filtered_items,
    const std::string& kernel_source) {
    const auto start_time = std::chrono::high_resolution_clock::now();

    cl_platform_id platform;
    cl_device_id device;

    // Get platform
    cl_int err = clGetPlatformIDs(1, &platform, nullptr);
    if (err != CL_SUCCESS) {
        std::cerr << "Failed to get platform" << std::endl;
        return;
    }

    // Get device (prefer GPU, fallback to CPU)
    err = clGetDeviceIDs(platform, CL_DEVICE_TYPE_GPU, 1, &device, nullptr);
    if (err != CL_SUCCESS) {
        err = clGetDeviceIDs(platform, CL_DEVICE_TYPE_CPU, 1, &device, nullptr);
        if (err != CL_SUCCESS) {
            std::cerr << "Failed to get device" << std::endl;
            return;
        }
    }

    // Print device info
    char device_name[128];
    char platform_name[128];
    clGetDeviceInfo(device,
        CL_DEVICE_NAME,
        sizeof(device_name),
        device_name,
        nullptr);
    clGetPlatformInfo(platform,
        CL_PLATFORM_NAME,
        sizeof(platform_name),
        platform_name,
        nullptr);
    std::cout << "OpenCL Platform: " << platform_name << std::endl;
    std::cout << "OpenCL Device: " << device_name << std::endl;

    // Create context
    cl_context context = clCreateContext(nullptr,
        1,
        &device,
        nullptr,
        nullptr,
        &err);
    if (err != CL_SUCCESS) {
        std::cerr << "Failed to create context" << std::endl;
        return;
    }

    // Create command queue
    cl_command_queue queue = clCreateCommandQueueWithProperties(context,
        device,
        nullptr,
        &err);
    if (err != CL_SUCCESS) {
        std::cerr << "Failed to create command queue" << std::endl;
        clReleaseContext(context);
        return;
    }
    const char* source_str = kernel_source.c_str();

    // Create program
    cl_program program = clCreateProgramWithSource(context,
        1,
        &source_str,
        nullptr,
        &err);
    if (err != CL_SUCCESS) {
        std::cerr << "Failed to create program" << std::endl;
        clReleaseCommandQueue(queue);
        clReleaseContext(context);
        return;
    }

    // Build program
    err = clBuildProgram(program, 1, &device, nullptr, nullptr, nullptr);
    if (err != CL_SUCCESS) {
        std::cerr << "Failed to build program" << std::endl;
        char build_log[4096];
        clGetProgramBuildInfo(program,
            device,
            CL_PROGRAM_BUILD_LOG,
            sizeof(build_log),
            build_log,
            nullptr);
        std::cerr << "Build log: " << build_log << std::endl;
        clReleaseProgram(program);
        clReleaseCommandQueue(queue);
        clReleaseContext(context);
        return;
    }

    // Create kernel
    // vienas workeris
    // cl_kernel kernel = clCreateKernel(program, "process_items_single", &err);

    cl_kernel kernel = clCreateKernel(program, "process_items", &err);

    if (err != CL_SUCCESS) {
        std::cerr << "Failed to create kernel" << std::endl;
        clReleaseProgram(program);
        clReleaseCommandQueue(queue);
        clReleaseContext(context);
        return;
    }

    // Prepare data
    std::vector<cl_int> quantities;
    std::vector<float> prices;
    std::vector<int> indexes(items.size(), -1);
    std::vector output_count(1, 0);

    for (const auto& item : items) {
        quantities.push_back(item.quantity);
        prices.push_back(static_cast<float>(item.price));
    }

    std::vector<unsigned int> results(items.size(), 0);

    // Create buffers
    cl_mem qty_buffer = clCreateBuffer(context,
        CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
        sizeof(cl_int) * quantities.size(),
        quantities.data(),
        &err);
    cl_mem result_buffer = clCreateBuffer(context,
        CL_MEM_WRITE_ONLY,
        sizeof(unsigned int) * results.size(),
        nullptr,
        &err);
    cl_mem index_buffer = clCreateBuffer(context,
        CL_MEM_READ_WRITE | CL_MEM_COPY_HOST_PTR,
        sizeof(int) * indexes.size(),
        indexes.data(),
        &err);
    cl_mem output_count_buffer = clCreateBuffer(context,
        CL_MEM_READ_WRITE | CL_MEM_COPY_HOST_PTR,
        sizeof(cl_int),
        output_count.data(),
        &err);

    // Set kernel arguments
    int count = static_cast<int>(items.size());
    clSetKernelArg(kernel, 0, sizeof(cl_mem), &qty_buffer);
    clSetKernelArg(kernel, 1, sizeof(cl_mem), &result_buffer);
    clSetKernelArg(kernel, 2, sizeof(cl_mem), &index_buffer);
    clSetKernelArg(kernel, 3, sizeof(cl_mem), &output_count_buffer);
    clSetKernelArg(kernel, 4, sizeof(cl_int), &count);

    // Execute kernel
    size_t global_size = items.size();
    // size_t global_size = 1;
    // vienas workeris
    err = clEnqueueNDRangeKernel(queue,
        kernel,
        1,
        nullptr,
        &global_size,
        nullptr,
        0,
        nullptr,
        nullptr);
    if (err != CL_SUCCESS) {
        std::cerr << "Failed to execute kernel: " << err << std::endl;
    }

    clFinish(queue);

    // Read results
    clEnqueueReadBuffer(queue,
        result_buffer,
        CL_TRUE,
        0,
        sizeof(unsigned int) * results.size(),
        results.data(),
        0,
        nullptr,
        nullptr);
    clEnqueueReadBuffer(queue,
        index_buffer,
        CL_TRUE,
        0,
        sizeof(int) * indexes.size(),
        indexes.data(),
        0,
        nullptr,
        nullptr);
    clEnqueueReadBuffer(queue,
        output_count_buffer,
        CL_TRUE,
        0,
        sizeof(cl_int) * output_count.size(),
        output_count.data(),
        0,
        nullptr,
        nullptr);

    std::cout << "OpenCL filtered items count: "
    << output_count[0] << std::endl;
    std::cout << "result buffer size: " << results.size() << std::endl;
    for (auto& rez : results) {
        std::cout << "result: " << rez << std::endl;
    }
    // Store results
    for (int i = 0; i < output_count[0]; i++) {
        int org_index = indexes[i];
        if (org_index >= 0 && org_index < static_cast<int>(items.size())) {
            FoodItem item = items[org_index];
            item.opencl_result = results[i];
            filtered_items.push_back(item);
        }
    }

    // Cleanup
    clReleaseMemObject(qty_buffer);
    clReleaseMemObject(result_buffer);
    clReleaseMemObject(index_buffer);
    clReleaseMemObject(output_count_buffer);
    clReleaseKernel(kernel);
    clReleaseProgram(program);
    clReleaseCommandQueue(queue);
    clReleaseContext(context);

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    std::cout << "OpenCL thread completed in "
    << duration.count() << " ms"
    << std::endl;
}

// Python sender thread
void pythonSender(const std::vector<FoodItem>& items) {
    auto start_time = std::chrono::high_resolution_clock::now();

#ifdef _WIN32
    WSADATA wsa_data;
    WSAStartup(MAKEWORD(2, 2), &wsa_data);
#endif

    SOCKET sock = socket(AF_INET, SOCK_STREAM, 0);

    sockaddr_in server_addr{};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(5001);
    inet_pton(AF_INET, "127.0.0.1", &server_addr.sin_addr);

    // Retry connection
    int attempts = 0;
    while (connect(sock,
        reinterpret_cast<sockaddr *>(&server_addr),
        sizeof(server_addr)) < 0 && attempts < 10) {
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        attempts++;
    }

    if (attempts >= 10) {
        std::cerr << "Failed to connect to Python receiver" << std::endl;
#ifdef _WIN32
        closesocket(sock);
#else
        close(sock);
#endif
        return;
    }

    std::cout << "Connected to Python receiver" << std::endl;

    // Send filtered items
    for (const auto& item : items) {
        std::string message = item.name + "," + std::to_string(item.quantity) +
                             "," + std::to_string(item.price) + "\n";
        send(sock, message.c_str(), static_cast<int>(message.length()), 0);
    }

    // Send end signal
    std::string end_msg = "END\n";
    send(sock, end_msg.c_str(), static_cast<int>(end_msg.length()), 0);

#ifdef _WIN32
    closesocket(sock);
    WSACleanup();
#else
    close(sock);
#endif

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    std::cout << "Python sender completed in "
    << duration.count() << " ms"
    << std::endl;
}

// Python receiver thread
void pythonReceiver(std::vector<FoodItem>& items) {
    auto start_time = std::chrono::high_resolution_clock::now();

#ifdef _WIN32
    WSADATA wsa_data;
    WSAStartup(MAKEWORD(2, 2), &wsa_data);
#endif

    SOCKET server_sock = socket(AF_INET, SOCK_STREAM, 0);

    int opt = 1;
    setsockopt(server_sock,
        SOL_SOCKET,
        SO_REUSEADDR,
        reinterpret_cast<char *>(&opt),
        sizeof(opt));

    sockaddr_in server_addr{};
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(5002);

    if (bind(server_sock,
        reinterpret_cast<sockaddr *>(&server_addr),
        sizeof(server_addr)) < 0) {
        std::cerr << "Failed to bind receiver socket" << std::endl;
#ifdef _WIN32
        closesocket(server_sock);
#else
        close(server_sock);
#endif
        return;
    }

    listen(server_sock, 1);
    std::cout << "Waiting for Python sender connection..." << std::endl;

    sockaddr_in client_addr{};
    socklen_t client_len = sizeof(client_addr);
    SOCKET client_sock = accept(server_sock,
        reinterpret_cast<sockaddr *>(&client_addr),
        &client_len);

    std::cout << "Python sender connected" << std::endl;

    // Receive results
    char buffer[4096];
    std::string accumulated;

    while (true) {
        int bytes = recv(client_sock, buffer, sizeof(buffer) - 1, 0);
        if (bytes <= 0) break;

        buffer[bytes] = '\0';
        accumulated += buffer;

        size_t pos;
        while ((pos = accumulated.find('\n')) != std::string::npos) {
            std::string line = accumulated.substr(0, pos);
            accumulated = accumulated.substr(pos + 1);

            if (line == "END") {
                goto finish_receive;
            }

            // Parse: name,result
            size_t comma = line.find(',');
            if (comma != std::string::npos) {
                std::string name = line.substr(0, comma);
                items.push_back({name,
                    0,
                    0.0,
                    0,
                    std::stod(line.substr(comma + 1))});
            }
        }
    }

finish_receive:
#ifdef _WIN32
    closesocket(client_sock);
    closesocket(server_sock);
    WSACleanup();
#else
    close(client_sock);
    close(server_sock);
#endif

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    std::cout << "Python receiver completed in "
              << duration.count() << " ms" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <input_file.json>" << std::endl;
        return 1;
    }
    std::ifstream kernelFile;
    std::string kernelSource;

    kernelFile.open("kernel.cl");
    if (!kernelFile.is_open()) {
        std::cerr << "Failed to open kernel.cl" << std::endl;
        return 1;
    }

    std::stringstream ss;
    ss << kernelFile.rdbuf();

    kernelSource = ss.str();
    kernelFile.close();

    auto total_start = std::chrono::high_resolution_clock::now();

    std::string input_file = argv[1];
    std::cout << "Processing file: " << input_file << std::endl;

    // Parse input
    std::vector<FoodItem> items = parseJSON(input_file);
    std::cout << "Loaded " << items.size() << " items" << std::endl;

    std::vector<FoodItem> openclFiltered;
    std::vector<FoodItem> pythonFiltered;

    // Start threads
    std::thread opencl_t(openclThread,
        std::ref(items),
        std::ref(openclFiltered),
        kernelSource);
    std::thread sender_t(pythonSender, std::ref(items));
    std::thread receiver_t(pythonReceiver, std::ref(pythonFiltered));

    // Wait for completion
    opencl_t.join();
    sender_t.join();
    receiver_t.join();

    std::vector<FoodItem> filtered_items;
    // Merge results
    for (auto& cl_item : openclFiltered) {
        for (auto& python_item : pythonFiltered) {
            if (cl_item.name == python_item.name) {
                cl_item.python_result = python_item.python_result;
                filtered_items.push_back(cl_item);
                break;
            }
        }
    }

    // Write results
    std::string output_file = "results.txt";
    std::ofstream out(output_file);

    out << std::string(50, '=') << "\n";
    out << "                    FOOD PROCESSING RESULTS\n";
    out << std::string(50, '=') << "\n";

    out << "Filter 1: Quantity >= 20\n";
    out << "Filter 2: Price >= 2.0\n\n";

    out << std::string(80, '-') << "\n";
    out << std::left << std::setw(20) << "Name"
        << std::setw(12) << "Quantity"
        << std::setw(12) << "Price"
        << std::setw(18) << "OpenCL Hash"
        << std::setw(18) << "Python Sum" << std::endl;
    out << std::left << std::string(80, '-') << "\n";

    for (const auto& item : filtered_items) {
        out << std::left << std::setw(20) << item.name
            << std::setw(12) << item.quantity
            << std::setw(12) << std::fixed << std::setprecision(2) << item.price
            << std::setw(18) << item.opencl_result
            << std::setw(18) << std::fixed
            << std::setprecision(2) << item.python_result
            << "\n";
    }

    out << std::string(80, '-') << "\n";
    out << "Total items processed: " << filtered_items.size() << "\n";

    out.close();

    auto total_end = std::chrono::high_resolution_clock::now();
    auto total_duration = std::chrono::duration_cast<std::chrono::milliseconds>(total_end - total_start);
    std::cout << "\nResults written to: " << output_file << std::endl;
    std::cout << "Total execution time: "
        << total_duration.count() << " ms" << std::endl;

    return 0;
}