import queue, time


'''
    简化版的短期记忆模块,支持基于SlidingWindow的记忆压缩(保留最新记忆)
'''
class Memory():
    def __init__(self, max_window_in_seconds, max_count):
        self.context_memory = {}
        self.overwrite_memory = {}
        self.max_window_in_seconds = max_window_in_seconds

    def get_overwrite_memory(self, conv_id, tag):
        if conv_id in self.overwrite_memory and tag in self.overwrite_memory[conv_id]:
            return self.overwrite_memory[conv_id][tag]
        return None
    
    def set_overwrite_memory(self, conv_id, tag, mem):
        if conv_id not in self.overwrite_memory:
            self.overwrite_memory[conv_id] = {tag : mem}
        else:
            self.overwrite_memory[conv_id][tag] = mem

    def add_memory(self, conv_id, mem) -> List[str]
        if conv_id not in self.context_memory:
            self.context_memory[conv_id] = queue.Queue()
        q = self.context_memory[conv_id]
        if time.time() - q.queue[0][0] >= self.max_window_in_seconds:
            q.get()
        q.put((time.time(), mem))
        return [v[1] for v in q.queue][-max_count:]


    def get_memory(self, conv_id) -> List[str]
        if conv_id in self.context_memory:
            q = self.context_memory[conv_id]
            if time.time() - q.queue[0][0] >= self.max_window_in_seconds:
                q.get()
            return [v[1] for v in q.queue][-max_count:]
        return None


    def clear_memory(self, conv_id) -> None:
        if conv_id in self.context_memory:
            delete(self.context_memory[conv_id])

