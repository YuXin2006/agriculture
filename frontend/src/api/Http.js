import axios from 'axios'
class Http {
    constructor() {
        this.instance = axios.create({
            baseURL: import.meta.env.VITE_BASE_URL || '',
            timeout: 6000
        })
        this.instance.interceptors.request.use(
            config => {
                const token = localStorage.getItem('token')
                if(token){
                    config.headers.Authorization='JWT '+token
                }
                return config
            })
        }
    post(path, data, options = {}) {
        //axios底层也是用的promise对象 相应的状态码不是200时就会调用reject，await会抛出异常
        return new Promise(async (resolve, reject) => {
            try{
                let result = await this.instance.post(path, data, options)
                resolve(result.data)
            }catch(err){
                let detail=err?.response?.data?.detail || err?.message || '请求失败'
                //console.log(err);
                reject(detail)
            }
        
        })
    }
    get(path,params) {
        return new Promise(async (resolve, reject) => {
            try{
                let result=await this.instance.get(path,{params})
                resolve(result.data)
            }catch(err){
                let detail=err?.response?.data?.detail || err?.message || '请求失败'
                reject(detail)
            }
        })
    }
    put(path,data){
        return new Promise(async (resolve, reject) => {
            try{
                let result=await this.instance.put(path,data)
                resolve(result.data)
            }catch(err){
                let detail=err?.response?.data?.detail || err?.message || '请求失败'
                reject(detail)
            }
        })
    }
    delete(path){
        return new Promise(async (resolve, reject) => {
            try{
                let result=await this.instance.delete(path)
                //服务器view的destroy方法返回的是一个response对象，并没有数据 所以这里直接返回result
                resolve(result)
            }catch(err){
                let detail=err?.response?.data?.detail || err?.message || '请求失败'
                reject(detail)
            }
        })
    }
   
}
export default new Http()