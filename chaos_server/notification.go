package main

type TriggerNotification interface {
	getBlockingCh() chan string
}

type TimeoutNotification struct {
	conditionName string
}

func (n *TimeoutNotification) getBlockingCh() chan string {
	return nil
}

type AnnotatedAPICallNotification struct {
	module       string
	filePath     string
	receiverType string
	funName      string
	observedWhen string
	observedBy   string
	blockingCh   chan string
}

func (n *AnnotatedAPICallNotification) getBlockingCh() chan string {
	return n.blockingCh
}

type ObjectCreateNotification struct {
	resourceKey  string
	observedWhen string
	observedBy   string
	blockingCh   chan string
}

func (n *ObjectCreateNotification) getBlockingCh() chan string {
	return n.blockingCh
}

type ObjectDeleteNotification struct {
	resourceKey  string
	observedWhen string
	observedBy   string
	blockingCh   chan string
}

func (n *ObjectDeleteNotification) getBlockingCh() chan string {
	return n.blockingCh
}

type ObjectUpdateNotification struct {
	resourceKey  string
	observedWhen string
	observedBy   string
	prevState    map[string]interface{}
	curState     map[string]interface{}
	blockingCh   chan string
}

func (n *ObjectUpdateNotification) getBlockingCh() chan string {
	return n.blockingCh
}

type AsyncDoneNotification struct {
}

const (
	UpdateTestPlan = iota
)

type ChaosSvrNotification interface {
	getBlockingCh() chan string
	getNotificationType() int
}

type UpdateTestPlanNotification struct {
	notificationType int
	runImmediatelyCount int
	blockingCh       chan string
	isForced 		bool
}

func (n *UpdateTestPlanNotification) getBlockingCh() chan string {
	return n.blockingCh
}

func (n *UpdateTestPlanNotification) getNotificationType() int {
	return n.notificationType
}

func (n *UpdateTestPlanNotification) getRunImmediatelyCount() int {
	return n.runImmediatelyCount
}

func (n *UpdateTestPlanNotification) getIsForced() bool {
	return n.isForced
}
