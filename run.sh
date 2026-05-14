#启动所有模型实例
#用于agent
jq -r '.agent.port.instance[]' conf/model.json | while IFS= read -r port; do
    nohup python model/model_instance.py agent $port &
done
#用于embedding
jq -r '.用于embedding.port.instance[]' conf/model.json | while IFS= read -r port; do
    nohup python model/model_instance.py embedding $port &
done
#用于rerank
jq -r '.rerank.port.instance[]' conf/model.json | while IFS= read -r port; do
    nohup python model/model_instance.py rerank $port &
done

#启动所有agent服务实例
jq -r '.port.instance[]' conf/app.json | while IFS= read -r port; do
    nohup python core/service.py $port &
done

#启动agent路由服务
route_port=`jq -r '.port.route' conf/app.json`
python service_route.py $route_port