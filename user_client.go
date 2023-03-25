package main

import (
	"fmt"
	"net/rpc"
	"os"
	"strconv"
	"sieve.client"
)

func main() {
	var labName string
	var force bool
	var runImmediatelyCount int
	labName = os.Args[1]
	runImmediatelyCount, _ = strconv.Atoi(os.Args[2])
	if os.Args[3] == "1" {
		force = true
	} else {
		force = false
	}
	hostPort := labName + "-control-plane:12345"
	rpcClient, err := rpc.Dial("tcp", hostPort)
	if err != nil {
		fmt.Printf("error in setting up connection to %s due to %v\n", hostPort, err)
		return
	}
	request := sieve.UpdateTestPlanRequest{
		RunImmediatelyCount: runImmediatelyCount,
		IsForce: force,
	}
	var response sieve.Response
	err = rpcClient.Call("TestCoordinator.UpdateTestPlanAPICall", request, &response)
	if err != nil {
		fmt.Println("RPCCall Failed", err)
		return
	}
	fmt.Println(response.Number)
}
