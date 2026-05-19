#启动所有模型实例
#start all model instances
#用于agent
#used for agent
jq -r '.agent.port.instance[]' conf/model.json | while IFS= read -r port; do
    nohup python model/model_instance.py agent $port &
done
#用于embedding
#used for RAG embedding
jq -r '.用于embedding.port.instance[]' conf/model.json | while IFS= read -r port; do
    nohup python model/model_instance.py embedding $port &
done
#用于rerank
#used for RAG rerank
jq -r '.rerank.port.instance[]' conf/model.json | while IFS= read -r port; do
    nohup python model/model_instance.py rerank $port &
done

#启动所有agent服务实例
#start all agent service instances
jq -r '.port.instance[]' conf/app.json | while IFS= read -r port; do
    nohup python core/service.py $port &
done

#启动agent路由服务
#start agent routing service
route_port=`jq -r '.port.route' conf/app.json`
python service_route.py $route_port