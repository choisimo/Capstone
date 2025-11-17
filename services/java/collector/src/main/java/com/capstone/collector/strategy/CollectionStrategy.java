package com.capstone.collector.strategy;

import com.capstone.collector.entity.DataSourceEntity;

import java.util.concurrent.CompletableFuture;

public interface CollectionStrategy {
    boolean supports(String sourceType);
    CompletableFuture<Integer> collect(DataSourceEntity source);
}
