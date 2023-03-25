package main

import (
	"log"
)

type ChaosServer struct {
	stateMachine      *StateMachine
	svrNotificationCh chan ChaosSvrNotification
}

func NewChaosServer(svrNotificationCh chan ChaosSvrNotification, sm *StateMachine) *ChaosServer {
	return &ChaosServer{
		stateMachine:      sm,
		svrNotificationCh: svrNotificationCh,
	}
}

func (cs *ChaosServer) updateTestPlan(notification ChaosSvrNotification) {
	ret := "0"
	defer func() {
		if blockingCh := notification.getBlockingCh(); blockingCh != nil {
			log.Println("release the blocking ch")
			blockingCh <- ret
		}
	}()

	config := getConfig()
	testPlan := parseTestPlan(config)
	ret = cs.stateMachine.UpdateStates(testPlan)
	log.Println("update states success")
	log.Println(testPlan)
}

func (cs *ChaosServer) handler(notification ChaosSvrNotification) {
	if notification.getNotificationType() == UpdateTestPlan {
		cs.updateTestPlan(notification)
	}
}

func (cs *ChaosServer) run() {
	for {
		select {
		case notification := <-cs.svrNotificationCh:
			cs.handler(notification)
		}
	}
}
