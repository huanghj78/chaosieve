module chaos_server

go 1.16

replace sieve.client => ../sieve_client

require (
	gopkg.in/yaml.v2 v2.4.0
	k8s.io/api v0.25.4
	k8s.io/apimachinery v0.25.4
	k8s.io/client-go v0.25.4
	sieve.client v0.0.0-00010101000000-000000000000
)
