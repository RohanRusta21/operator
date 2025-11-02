import kopf
import kubernetes as k8s
import os

# Configure Kubernetes client
try:
    k8s.config.load_incluster_config()  # For running inside cluster
except k8s.config.ConfigException:
    k8s.config.load_kube_config()  # For local development

@kopf.on.create('rohan.com', 'v1', 'mypods')
def create_pod(body, spec, **kwargs):
    name = body['metadata']['name']
    namespace = body['metadata']['namespace']
    image = spec.get('image', 'nginx')
    replicas = spec.get('replicas', 1)

    api = k8s.client.CoreV1Api()
    
    created_pods = []
    
    for i in range(replicas):
        pod_name = f"{name}-pod-{i}"
        
        pod = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': pod_name,
                'namespace': namespace,
                'labels': {
                    'app': name,
                    'created-by': 'mypod-operator'
                }
            },
            'spec': {
                'containers': [{
                    'name': 'main',
                    'image': image,
                    'imagePullPolicy': 'IfNotPresent'
                }],
                'restartPolicy': 'Always'
            },
        }
        
        try:
            api.create_namespaced_pod(namespace=namespace, body=pod)
            created_pods.append(pod_name)
            print(f"Successfully created pod: {pod_name}")
        except k8s.client.exceptions.ApiException as e:
            print(f"Failed to create pod {pod_name}: {e}")
            raise kopf.PermanentError(f"Failed to create pod: {e}")

    return {'message': f'Successfully created {len(created_pods)} pods: {", ".join(created_pods)}'}

@kopf.on.delete('rohan.com', 'v1', 'mypods')
def delete_pods(body, **kwargs):
    name = body['metadata']['name']
    namespace = body['metadata']['namespace']
    
    api = k8s.client.CoreV1Api()
    
    # Delete pods created by this MyPod resource
    label_selector = f"created-by=mypod-operator,app={name}"
    
    try:
        pods = api.list_namespaced_pod(
            namespace=namespace, 
            label_selector=label_selector
        )
        
        for pod in pods.items:
            api.delete_namespaced_pod(
                name=pod.metadata.name,
                namespace=namespace
            )
            print(f"Deleted pod: {pod.metadata.name}")
            
    except k8s.client.exceptions.ApiException as e:
        print(f"Error deleting pods: {e}")

if __name__ == '__main__':
    kopf.run()