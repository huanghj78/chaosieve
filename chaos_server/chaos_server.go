package main

import (
	"fmt"
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

func (cs *ChaosServer) updateTestPlan(notification *UpdateTestPlanNotification) {
	ret := "Success"
	defer func() {
		if blockingCh := notification.getBlockingCh(); blockingCh != nil {
			log.Println("release the blocking ch")
			blockingCh <- ret
		}
	}()
	config := getConfig()
	testPlan := parseTestPlan(config)
	if err := cs.stateMachine.UpdateStates(testPlan, notification.getRunImmediatelyCount(), notification.getIsForced()); err != nil {
		ret = fmt.Sprintf("%s", err)
	}
	log.Println(testPlan)
}

func (cs *ChaosServer) handler(notification ChaosSvrNotification) {
	if notification.getNotificationType() == UpdateTestPlan {
		v, ok := notification.(*UpdateTestPlanNotification)
		if ok {
			cs.updateTestPlan(v)
		} else {
			log.Println("!!!!!")
		}

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
