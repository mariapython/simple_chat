# simple_chat

## usage:
1. Start redis server
2. Join chat:

  ```
  > python dechat <port of chat member 1> <usr chat member 1>
  > python dechat <port chat member 2> <usr chat member 2>
  ...
  ```
3. read message logs: 

  ```
  lrange chat_logs 0 <no of messages sent>
  ```
