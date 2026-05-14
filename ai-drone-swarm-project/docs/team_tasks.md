# Team Tasks

## Member 1 — Object Detection

### Deliverables
- YOLO detection script
- Detection output in JSON format
- Demo with webcam/image/video
- Short README explaining how to run

### Completion Criteria
- The script detects at least one object class.
- The output follows the common message format.
- Results can be used by the communication module.

---

## Member 2 — MQTT Communication

### Deliverables
- MQTT publisher
- MQTT subscriber
- Broker setup instructions
- Demo of message exchange between two clients

### Completion Criteria
- One script publishes detection messages.
- Another script receives messages.
- Messages are valid JSON.
- Received messages can be forwarded to the LLM module.

---

## Member 3 — LLM Decision Module

### Deliverables
- Prompt builder
- Decision function
- Rule-based fallback
- Test scenarios
- JSONL examples for possible fine-tuning/evaluation

### Completion Criteria
- The module receives a detection message.
- The module returns risk level, action, recommendation and broadcast flag.
- Fallback works without a real LLM.
- The module can be connected to MQTT subscriber.

---

## Member 4 — ROS2/Gazebo Simulation & Integration

### Deliverables
- ROS2/Gazebo setup notes
- Suggested nodes and topics
- Multi-drone namespace plan
- Integration demo pipeline

### Completion Criteria
- Project architecture is documented.
- Simulation structure is ready.
- Modules can be connected logically.
- Demo pipeline shows full system flow.
