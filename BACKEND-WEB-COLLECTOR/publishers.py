from __future__ import annotations
import json
import os
import sys
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PublishResult:
    ok: bool
    error: Optional[str] = None


class Publisher:
    def publish(self, topic: str, key: Optional[bytes], value: bytes, headers: Dict[str, str]) -> PublishResult:
        raise NotImplementedError


class StdoutPublisher(Publisher):
    def publish(self, topic: str, key: Optional[bytes], value: bytes, headers: Dict[str, str]) -> PublishResult:
        try:
            record = {
                "topic": topic,
                "key": key.hex() if key else None,
                "headers": headers,
                "value": json.loads(value.decode("utf-8")),
            }
            print(json.dumps(record, ensure_ascii=False))
            return PublishResult(ok=True)
        except Exception as e:
            print(f"stdout publish error: {e}", file=sys.stderr)
            return PublishResult(ok=False, error=str(e))


class KafkaPublisher(Publisher):
    def __init__(self, brokers: str):
        self._producer = None
        self._err: Optional[str] = None
        # Prefer confluent-kafka, fallback to kafka-python
        try:
            from confluent_kafka import Producer  # type: ignore

            self._impl = "confluent"
            self._producer = Producer({"bootstrap.servers": brokers})
        except Exception:
            try:
                from kafka import KafkaProducer  # type: ignore

                self._impl = "kafka-python"
                self._producer = KafkaProducer(bootstrap_servers=brokers, value_serializer=lambda v: v, key_serializer=lambda k: k)
            except Exception as e:
                self._err = (
                    "Kafka client not available. Install 'confluent-kafka' or 'kafka-python'. "
                    f"Init error: {e}"
                )

    def publish(self, topic: str, key: Optional[bytes], value: bytes, headers: Dict[str, str]) -> PublishResult:
        if self._err:
            return PublishResult(ok=False, error=self._err)
        try:
            if self._impl == "confluent":
                assert self._producer is not None
                hdrs = [(k, v.encode("utf-8")) for k, v in headers.items()]
                self._producer.produce(topic=topic, key=key, value=value, headers=hdrs)
                self._producer.poll(0)
            else:
                assert self._producer is not None
                # kafka-python expects list of tuples for headers
                hdrs = [(k, v.encode("utf-8")) for k, v in headers.items()]
                self._producer.send(topic, key=key, value=value, headers=hdrs)
            return PublishResult(ok=True)
        except Exception as e:
            return PublishResult(ok=False, error=str(e))


class PubSubPublisher(Publisher):
    def __init__(self, project: str):
        try:
            from google.cloud import pubsub_v1  # type: ignore

            self._publisher = pubsub_v1.PublisherClient()
            self._project = project
        except Exception as e:
            self._publisher = None
            self._project = project
            self._err = (
                "Pub/Sub client not available. Install 'google-cloud-pubsub' and configure credentials. "
                f"Init error: {e}"
            )

    def publish(self, topic: str, key: Optional[bytes], value: bytes, headers: Dict[str, str]) -> PublishResult:
        if not hasattr(self, "_publisher") or self._publisher is None:
            return PublishResult(ok=False, error=getattr(self, "_err", "Pub/Sub client not available"))
        try:
            topic_path = self._publisher.topic_path(self._project, topic)
            future = self._publisher.publish(topic_path, data=value, **headers)
            future.result(timeout=30)
            return PublishResult(ok=True)
        except Exception as e:
            return PublishResult(ok=False, error=str(e))


def make_publisher(bus: str, kafka_brokers: Optional[str], pubsub_project: Optional[str]) -> Publisher:
    if bus == "kafka" and kafka_brokers:
        return KafkaPublisher(kafka_brokers)
    if bus == "pubsub" and pubsub_project:
        return PubSubPublisher(pubsub_project)
    return StdoutPublisher()
