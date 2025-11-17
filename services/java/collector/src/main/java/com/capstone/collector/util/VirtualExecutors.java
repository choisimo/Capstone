package com.capstone.collector.util;

import java.lang.reflect.Method;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class VirtualExecutors {
    private VirtualExecutors() {}

    /**
     * Creates a virtual-thread-per-task executor when running on Java 21+.
     * Falls back to cached thread pool on older JDKs.
     */
    public static ExecutorService newVirtualPerTaskOrCached() {
        try {
            Class<?> execClass = Class.forName("java.util.concurrent.Executors");
            Method m = execClass.getMethod("newVirtualThreadPerTaskExecutor");
            Object executor = m.invoke(null);
            return (ExecutorService) executor;
        } catch (Throwable t) {
            // JDK < 21 or reflection failed
            return Executors.newCachedThreadPool();
        }
    }
}
