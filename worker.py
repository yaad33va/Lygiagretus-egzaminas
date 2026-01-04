"""
Python worker
"""
import socket
import multiprocessing
import time
import queue


def complex_computation(quantity: int, price: float) -> float:
    """
        Simulates a complex computation.
     Args:
        quantity: Quantity of the food
        price: Cost of the food
    """
    result = float(quantity + price * 100)

    for i in range(1000000):
        result = (result * 1.103515245 + 12345.0) % (2**31)
        result = result / 1000000.0 + quantity + price
        result = abs(result)
        temp = result * 2654435761.0
        result = (temp % 1000000) + quantity * (i % 10 + 1)

    return result


def worker_process(input_queue: multiprocessing.Queue,
                   output_queue: multiprocessing.Queue,
                   worker_id: int) -> None:
    """
    Receives items, processes them, and sends results.

    Args:
        input_queue: Queue to receive work items from
        output_queue: Queue to send results to
        worker_id: Unique identifier for this worker
    """
    print(f"Worker {worker_id} started")
    items_processed = 0

    while True:
        try:
            item = input_queue.get(timeout=2)

            if item == "STOP":
                print(f"Worker {worker_id} received stop signal after {items_processed} items")
                output_queue.put("WORKER_DONE")
                break

            name, quantity, price = item
            result = complex_computation(quantity, price)
            if price >= 2.0:
                output_queue.put((name, result))
                items_processed += 1

        except queue.Empty:
            continue
        except (ValueError, TypeError) as e:
            print(f"Worker {worker_id} error: {e}")
            continue

    print(f"Worker {worker_id} finished")


def receiver_process(input_queue: multiprocessing.Queue) -> None:
    """
    Receives data from C++ program via network and distributes to workers.

    Args:
        input_queue: Queue to send work items to workers
    """
    print("Receiver process started")

    # Create socket server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('127.0.0.1', 5001))
    server_socket.listen(1)

    print("Waiting for C++ sender connection on port 5001...")
    client_socket, address = server_socket.accept()
    print(f"Connected to C++ sender: {address}")

    buffer = ""
    items_received = 0

    try:
        while True:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                break

            buffer += data

            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()

                if line == "END":
                    print(f"Received END signal. Total items: {items_received}")
                    client_socket.close()
                    server_socket.close()
                    print("Receiver process finished")
                    return

                if not line:
                    continue

                try:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        name = parts[0]
                        quantity = int(parts[1])
                        price = float(parts[2])

                        input_queue.put((name, quantity, price))
                        items_received += 1
                except ValueError as e:
                    print(f"Error parsing line '{line}': {e}")

    except OSError as e:
        print(f"Receiver error: {e}")
    finally:
        client_socket.close()
        server_socket.close()

    print("Receiver process finished")


def sender_process(output_queue: multiprocessing.Queue, num_workers: int) -> None:
    """
    Collects results from workers and sends them to C++ program via network.

    Args:
        output_queue: Queue to receive results from workers
        num_workers: Number of worker processes to wait for
    """
    print("Sender process started")

    time.sleep(1)

    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    attempts = 0
    while attempts < 20:
        try:
            sender_socket.connect(('127.0.0.1', 5002))
            print("Connected to C++ receiver on port 5002")
            break
        except ConnectionRefusedError:
            attempts += 1
            time.sleep(0.5)

    if attempts >= 20:
        print("Failed to connect to C++ receiver")
        return

    results_sent = 0
    workers_finished = 0

    try:
        while workers_finished < num_workers:
            try:
                result = output_queue.get(timeout=2)

                if result == "WORKER_DONE":
                    workers_finished += 1
                    print(f"Workers finished: {workers_finished}/{num_workers}")
                    continue

                name, value = result
                message = f"{name},{value:.2f}\n"
                sender_socket.send(message.encode('utf-8'))
                results_sent += 1

            except queue.Empty:
                continue
            except OSError as e:
                print(f"Sender error getting from queue: {e}")
                continue

    except OSError as e:
        print(f"Sender error: {e}")

    # Send end signal
    sender_socket.send(b"END\n")
    print(f"Sender sent {results_sent} results")
    sender_socket.close()
    print("Sender process finished")


def main():
    """Main function to coordinate all processes."""
    start_time = time.time()

    num_workers = max(1, multiprocessing.cpu_count() - 1)
    # Vienas workeris
    # num_workers = 1

    print(f"Starting with {num_workers} worker processes")

    input_queue = multiprocessing.Queue()
    output_queue = multiprocessing.Queue()

    workers = []
    for i in range(num_workers):
        worker = multiprocessing.Process(
            target=worker_process,
            args=(input_queue, output_queue, i)
        )
        workers.append(worker)
        worker.start()

    receiver = multiprocessing.Process(
        target=receiver_process,
        args=(input_queue,)
    )
    receiver.start()

    sender = multiprocessing.Process(
        target=sender_process,
        args=(output_queue, num_workers)
    )
    sender.start()

    receiver.join()
    print("Receiver joined")

    print(f"Main process sending STOP signals to {num_workers} workers")
    for i in range(num_workers):
        input_queue.put("STOP")
        print(f"Main sent STOP to worker {i}")

    sender.join()
    print("Sender joined")

    for i, worker in enumerate(workers):
        worker.join(timeout=5)
        if worker.is_alive():
            print(f"Worker {i} didn't finish, terminating...")
            worker.terminate()
    print("All workers joined")

    end_time = time.time()
    print(f"\nPython program completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    main()