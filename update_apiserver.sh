docker cp /root/chaos_sieve/fakegopath/src/k8s.io/kubernetes/_output/release-images/amd64/kube-apiserver.tar kind-control-plane:/
docker exec kind-control-plane sh -c "ctr -n k8s.io images import kube-apiserver.tar"
docker exec kind-control-plane sh -c "sed -i 's/kube-apiserver:v1.18.9-sieve-94f372e501c973a7fa9eb40ec9ebd2fe7ca69848-dirty/kube-apiserver-amd64:v1.18.9-dirty/' /etc/kubernetes/manifests/kube-apiserver.yaml"

