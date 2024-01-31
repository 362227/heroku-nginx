import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 代理
proxy = {'http': 'http://127.0.0.1:1086', 'https': 'http://127.0.0.1:1086'}

# 需要尝试的链接列表


urls = [
    "https://github.c/qodnh/?这是无效链接，让这个代码能无限循环", 
    "https://dc328d28-ef61-4e36-9b6d-040bb1384e09-00-3bjxvzmdvu0yu.sisko.replit.dev",
    "https://967d667b-f766-445e-a4dd-6cfaf4814e98-00-2srpxx0jsejis.pike.replit.dev",
    "https://109ef66c-c2f0-4345-8d15-47333a179e2e-00-1q1wc7w4fmtnq.sisko.replit.dev",
    "https://1616325f-23ff-469e-ba6a-1227e6bc9155-00-14uiu4b8ug72l.sisko.replit.dev",
    "https://b2a7c1ca-37cc-4f02-9656-8bd00e662f3f-00-39r5sxr4czym3.pike.replit.dev",
    "https://b9dc0bd1-a377-4b49-b51f-0ee53c458d30-00-3cko837imdl1x.pike.replit.dev", #006
    "https://418d13b4-66ab-447d-bc84-2f55955eb0a0-00-1ansofx0xaop3.pike.replit.dev",
    "https://0cd68126-a42c-4462-98f0-0772bdf5a633-00-3evk3tcly5ul6.pike.replit.dev",
    "https://690a829d-6ec1-4398-9135-74d6a47797fb-00-erbdketagsxu.sisko.replit.dev",
    "https://08dfa419-1e33-4304-8090-34b45898e918-00-2o5pwozmgmibl.sisko.replit.dev",#010

    #rgttta@hotmail.com
    "https://27a01819-dbc5-4bd3-8af4-86c227ba0e36-00-2h7tnbhr7ijub.kirk.replit.dev", #001
    "https://31a3a53d-2421-4a52-a3be-5dc7a46a8489-00-1j81lajxerd0n.kirk.replit.dev",
    "https://f822e367-500f-49de-8a3f-6f10a05799b7-00-2s73nnxsieubn.worf.replit.dev",
    "https://1e16f377-3769-41ec-a08c-e9d0fcd8209b-00-3d1n7rthu0xw.spock.replit.dev",
    "https://5d9b9b13-e024-4a5d-b903-0550152c670c-00-2e18itco2z3af.kirk.replit.dev",#005
    "https://3e90728b-899e-49e3-8771-8af5e984cb12-00-2mzs0vh65m0cd.picard.replit.dev",
    "https://613fa021-f42a-4951-9dcb-d5a1e95204f0-00-iyamzl49wkys.kirk.replit.dev",
    "https://c392e103-b1b5-42ed-853f-2c36877b6dfd-00-d57wjynhoa0t.riker.replit.dev",
    "https://baa350c4-f211-403a-b9b7-2324a3e633a8-00-y2b4n59p5vm6.kirk.replit.dev",
    "https://544cfef0-0123-4989-aa2f-038afa0ceb78-00-qp5ysznr8te7.kirk.replit.dev",

    #pizvjdeewlfzt@hotmail.com
    "https://95ba45ed-1939-442f-93bc-c5267c0de320-00-1u9jmnq7kdpmr.worf.replit.dev",
    "https://215d2ca8-cfcd-4839-8b07-b8ef6ab56493-00-2x68rh8htefn1.picard.replit.dev",
    "https://ae7d2c78-8cb3-4666-a485-feb2263697d2-00-kjvkp6yl7vws.worf.replit.dev",
    "https://d40547c6-043e-4b30-ac97-2685d4bf1d13-00-1lwg41prwc0sl.kirk.replit.dev",
    "https://e24f0172-82a3-45b2-88e9-7d3f49cfea6a-00-36keftxll3h66.worf.replit.dev",#5
    "https://1e52d4ba-2224-4b07-a512-2900c75389fd-00-17rkamgufgafo.spock.replit.dev",
    "https://13db71ee-3d92-4fab-9edd-242e1c4e83d3-00-2kkfxsqcief8e.picard.replit.dev",
    "https://1f9fc906-b151-48ea-b2a3-6f60e8410618-00-3euraaw2tz1zm.janeway.replit.dev",
    "https://c7605d2f-e5e1-44b8-88d3-4533e6d4a41a-00-2nle1ckc67358.worf.replit.dev",
    "https://66f0929d-0d27-4acd-b2e1-ca55113816cd-00-38xjxwqruff4d.worf.replit.dev",

    #lzywgycaew@hotmail.com
    "https://992b88f7-448a-40dd-8edb-046daf62a172-00-bocw5tm8ihqj.kirk.replit.dev",
    "https://7e6162f1-6dc8-40ac-a9d8-cf1b96e55f6b-00-1sm8wncgr4exb.worf.replit.dev",
    "https://48765636-6863-4060-8a4e-4c1e27ca854c-00-nspvgig715ah.picard.replit.dev",
    "https://1cbcae3c-bced-45c8-9748-dc2d4177bddb-00-30amd4ifl2s5k.janeway.replit.dev",
    "https://7a024403-b62b-4c0c-8ab0-a25dec4930eb-00-n30alnzyv0lh.spock.replit.dev",#5
    "https://6f195e37-2ec0-4e74-96af-7ab526678c8a-00-3p58xlsbehz8f.kirk.replit.dev",
    "https://f5e9888a-f148-4393-b227-a000deb762e8-00-3gyx1jukys308.spock.replit.dev",
    "https://85b7dd15-7ccc-4d66-92c2-34cfb6aecd38-00-wx411c8gq7tg.worf.replit.dev",
    "https://9e23479a-749b-4997-8b50-29dc4e5dc67c-00-1sw5o080h0ypx.worf.replit.dev",
    "https://2555c905-f039-4fc5-973f-5b8b5b420ab9-00-1w2maf8vk8i7u.spock.replit.dev",

    #mfuvqyfavxlzawd@hotmail.com
    "https://38b7a5e5-bc37-4881-a783-5d0b8dc85cf8-00-12l15nr4egv35.kirk.replit.dev",
    "https://20f5ed90-1a12-4c4b-a64f-57477653129b-00-3u07duawa2xuv.riker.replit.dev",
    "https://66056477-b0b8-4fbb-9446-ba11c4a7a440-00-2yo2207cx32eo.kirk.replit.dev",
    "https://4fafde8f-7c60-421d-8f56-050b2e65add3-00-2cgsl1zlw54wk.worf.replit.dev",
    "https://f7bf33b9-ad1e-4e06-8132-473711c9eb05-00-2icywl6l3ole6.janeway.replit.dev",#5
    "https://43f2b847-c456-4090-9930-71df65294e4e-00-28pniimli10s4.kirk.replit.dev",
    "https://8b62b4d4-8c3e-4724-8d00-e1618f6e3bbe-00-1jl87p9f3u6il.picard.replit.dev",
    "https://b054cd15-f4d9-4c57-a36c-0c0299f6b29e-00-vnjzaf5q0cou.janeway.replit.dev",
    "https://dc8706eb-8358-4853-abef-3713618b3232-00-whn89afw9v51.picard.replit.dev",
    "https://4e22895e-cdd2-4b69-84e2-b5f52d6efd1d-00-2v8n8b2paqsku.janeway.replit.dev",

    #tygtuocnwfsszf@hotmail.com
    "https://eae4bf65-df1e-4c64-97a8-2b40e1aceeab-00-18uhft6lrhtk.picard.replit.dev",
    "https://d1266bf0-9620-4944-8dd1-714461128c5c-00-3k0ddwhnu5ls8.kirk.replit.dev",
    "https://555d69a4-10c1-4a74-8b40-870b8ab6ef02-00-1m7gkudmnic39.spock.replit.dev",
    "https://ee592219-ba0e-4e70-a04f-6b259554793a-00-kxgs5pybfyx2.kirk.replit.dev",
    "https://278701eb-116a-4737-9e2b-b054056048e2-00-2bndcgv9sum83.spock.replit.dev",#5
    "https://ee0962e7-edbd-4e26-8ab0-7b35f2c0865b-00-3q6jrgmptu03a.kirk.replit.dev",
    "https://a4bd5faa-dbb1-491f-bdc8-4c668b3699f6-00-1nbxlvsfgs4y5.picard.replit.dev",
    "https://c854cbe6-86d5-408c-a9ca-5169ce4a3559-00-1syq16bbhxjp1.janeway.replit.dev",
    "https://b4cd3024-6e38-42f9-a1c1-0e0e0dd6d454-00-2bxogubyaae5z.kirk.replit.dev",
    "https://9fe59190-1672-4c8c-9af0-e0470ce6dc6b-00-2n9gr9uf7knqw.picard.replit.dev",

    #uegmuovbuwlryff@hotmail.com
    "https://9f6c8605-8a24-448c-a157-76332d558ec8-00-g1rrdbq6h4w0.picard.replit.dev",
    "https://2d7dba58-7fed-4ffa-bd12-29a468c10bf7-00-3doi0m1syy8z8.spock.replit.dev",
    "https://ccb24536-06e2-47dc-ad1a-5a3989ef0854-00-3iz3idwyltr1r.riker.replit.dev",
    "https://7781076a-71af-456f-95a1-d02a4a8152f1-00-2pqtfbeeizywu.picard.replit.dev",
    "https://e38b3898-00ac-4f1c-98f1-0858fce8956d-00-7wxez792ig1e.spock.replit.dev",#5
    "https://b47952d0-e1cf-4e11-9ba7-c601176a56fc-00-2xmjowg7p2zom.kirk.replit.dev",
    "https://f751ceab-864e-4973-b109-0c5b67c3ba00-00-kxf184gajppu.kirk.replit.dev",
    "https://99512786-f679-4ace-9578-d11c82acca87-00-127isyxtc5wp8.kirk.replit.dev",
    "https://3cb55a40-547a-40bc-9223-33900102f6be-00-3u2v9v1m6zcnf.kirk.replit.dev",
    "https://f7f28c01-5c68-49a4-a2a9-db7d80fd4aa8-00-24ipbfglxefsv.kirk.replit.dev",

    #mbvcjq@hotmail.com
    "https://ab81e36a-a53f-4fef-83df-f67f4bf042b2-00-2y7572qjyl42c.worf.replit.dev",
    "https://b80182f0-f249-4ec8-a266-43c376eadd36-00-200ul6v5pa9ig.kirk.replit.dev",
    "https://9ac4b2c4-e0d0-46d1-916f-78475c1622f0-00-yqatz1s7vtg2.riker.replit.dev",
    "https://1dd3ce7a-d4cb-4838-b7a8-4f836460a62d-00-viblyftsxrfu.worf.replit.dev",
    "https://6f316de2-20cc-48eb-9fd7-298667d0009e-00-1dgoylbh0boy2.kirk.replit.dev",#5
    "https://884f63f2-e1c8-4d47-8e04-00666668d4f7-00-1zks0e8slj008.spock.replit.dev",
    "https://d2f87ca5-0107-4711-86d4-839560e34f19-00-jg8pqez6qk5v.janeway.replit.dev",
    "https://50bd63d3-17bd-4f91-b147-5c87e141077d-00-mslx4s2jealp.worf.replit.dev",
    "https://742ce08a-6796-4fb6-9023-0262538f9faf-00-2vsa8rurouqw4.worf.replit.dev",
    "https://a14107fb-33b2-4e56-9884-1904099eb160-00-2agx836ew090e.spock.replit.dev",
]





'''
#偶数
urls = [
    "https://github.c/qodnh/?这是无效链接，让这个代码能无限循环", 
    "https://vimeo362227-2.onrender.com",
    "https://vimeo362227-4.onrender.com",
    "https://vimeo362227-6.onrender.com",
    "https://vimeo362227-8.onrender.com",
    "https://vimeo362227-10.onrender.com",
    "https://vimeo362227-12.onrender.com",
    "https://vimeo362227-14.onrender.com",
    "https://vimeo362227-16.onrender.com",
    "https://vimeo362227-18.onrender.com",
    "https://vimeo362227-20.onrender.com",
    "https://vimeo362227-22.onrender.com",
    "https://vimeo362227-24.onrender.com",
    "https://vimeo362227-26.onrender.com",
    "https://vimeo362227-28.onrender.com",
    "https://vimeo362227-30.onrender.com",
    "https://vimeo362227-32.onrender.com",
    "https://vimeo362227-34.onrender.com",
    "https://vimeo362227-36.onrender.com",
    "https://vimeo362227-38.onrender.com",
    "https://vimeo362227-40.onrender.com",
    "https://vimeo362227-42.onrender.com",
    "https://vimeo362227-44.onrender.com",
    "https://vimeo362227-46.onrender.com",
    "https://vimeo362227-48.onrender.com",
    "https://vimeo362227-50.onrender.com",
    "https://vimeo362227-52.onrender.com",
    "https://vimeo362227-54.onrender.com",
    "https://vimeo362227-56.onrender.com",
    "https://vimeo362227-58.onrender.com",
    "https://vimeo362227-60.onrender.com",
    "https://vimeo362227-62.onrender.com",
    "https://vimeo362227-64.onrender.com",
    "https://vimeo362227-66.onrender.com",
    "https://vimeo362227-68.onrender.com",
    "https://vimeo362227-70.onrender.com",
    "https://vimeo362227-72.onrender.com",
    "https://vimeo10362227-2.onrender.com",  
    "https://vimeo10362227-4.onrender.com",  
    "https://vimeo10362227-6.onrender.com",  
    "https://vimeo10362227-8.onrender.com",
    "https://vimeo10362227-10.onrender.com",  
    "https://vimeo10362227-12.onrender.com", 
    "https://vimeo10362227-14.onrender.com",  
    "https://vimeo10362227-16.onrender.com",  
    "https://vimeo10362227-18.onrender.com",  
    "https://vimeo10362227-20.onrender.com",  
    "https://vimeo10362227-22.onrender.com", 
    "https://vimeo10362227-24.onrender.com",  
    "https://vimeo10362227-26.onrender.com",  
    "https://vimeo10362227-28.onrender.com",  
    "https://vimeo10362227-30.onrender.com",  
    "https://vimeo10362227-32.onrender.com", 
    "https://vimeo10362227-34.onrender.com",  
    "https://vimeo10362227-36.onrender.com",  
    "https://vimeo10362227-38.onrender.com",  
    "https://vimeo10362227-40.onrender.com",  
    "https://vimeo10362227-42.onrender.com", 
    "https://vimeo10362227-44.onrender.com",  
    "https://vimeo10362227-46.onrender.com",  
    "https://vimeo10362227-48.onrender.com",  
    "https://vimeo10362227-50.onrender.com",  
    "https://vimeo10362227-52.onrender.com", 
    "https://vimeo10362227-54.onrender.com",  
    "https://vimeo10362227-56.onrender.com",  
    "https://vimeo10362227-58.onrender.com",  
    "https://vimeo10362227-60.onrender.com",  
    "https://vimeo10362227-62.onrender.com",  
    "https://vimeo10362227-64.onrender.com",  
    "https://vimeo10362227-66.onrender.com",  
    "https://vimeo10362227-68.onrender.com",  
    "https://vimeo10362227-70.onrender.com",
    "https://vimeo10362227-72.onrender.com",
    "https://vimeo10362227-74.onrender.com",

    
    "https://ellie002.onrender.com",
    "https://ellie004.onrender.com",
    "https://ellie006.onrender.com",
    "https://ellie008.onrender.com",
    "https://ellie010.onrender.com",
    "https://ellie012.onrender.com",
    "https://ellie014.onrender.com",
    "https://ellie016.onrender.com",
    "https://ellie018.onrender.com",
    "https://ellie020.onrender.com",
    "https://ellie022.onrender.com",
    "https://ellie024.onrender.com",
    "https://ellie026.onrender.com",
    "https://ellie028.onrender.com",
    "https://ellie030.onrender.com",
    "https://ellie032.onrender.com",
    "https://ellie034.onrender.com",
    "https://ellie036.onrender.com",
    "https://ellie038.onrender.com",
    "https://ellie040.onrender.com",
    "https://ellie042.onrender.com",
    "https://ellie044.onrender.com",
    "https://ellie046.onrender.com",
    "https://ellie048.onrender.com",
    "https://ellie050.onrender.com",
    "https://ellie052.onrender.com",
    "https://ellie054.onrender.com",
    "https://ellie056.onrender.com",
    "https://ellie058.onrender.com",
    "https://ellie060.onrender.com",
    "https://ellie062.onrender.com",
    "https://ellie064.onrender.com",
    "https://ellie066.onrender.com",
    "https://ellie068.onrender.com",
    "https://ellie070.onrender.com",
    "https://ellie072.onrender.com",
    "https://ellie074.onrender.com",
    "https://ellie076.onrender.com",  
    "https://ellie078.onrender.com",  
    "https://ellie080.onrender.com",  
    "https://ellie082.onrender.com",  
    "https://ellie084.onrender.com",  
    "https://ellie086.onrender.com",  
    "https://ellie088.onrender.com",  
    "https://ellie090.onrender.com",  
    "https://ellie092.onrender.com",  
    "https://ellie094.onrender.com",  
    "https://ellie096.onrender.com",  
    "https://ellie098.onrender.com",  
    "https://ellie100.onrender.com",  
    "https://ellie102.onrender.com",
    "https://ellie104.onrender.com",
    "https://kai006.onrender.com",
]
'''


'''
urls = [
        "https://vimeo362227.onrender.com",
    "https://vimeo362227-1.onrender.com",
    "https://vimeo362227-2.onrender.com",
    "https://vimeo362227-3.onrender.com",
    "https://vimeo362227-4.onrender.com",
    "https://vimeo362227-5.onrender.com",
    "https://vimeo362227-6.onrender.com",
    "https://vimeo362227-7.onrender.com",
    "https://vimeo362227-8.onrender.com",
    "https://vimeo362227-9.onrender.com",
    "https://vimeo362227-10.onrender.com",
    "https://vimeo362227-11.onrender.com",
    "https://vimeo362227-12.onrender.com",
    "https://vimeo362227-13.onrender.com",
    "https://vimeo362227-14.onrender.com",
    "https://vimeo362227-15.onrender.com",
    "https://vimeo362227-16.onrender.com",
    "https://vimeo362227-17.onrender.com",
    "https://vimeo362227-18.onrender.com",
    "https://vimeo362227-19-7hgu.onrender.com",
    "https://vimeo362227-20.onrender.com",
    "https://vimeo362227-21.onrender.com",
    "https://vimeo362227-22.onrender.com",
    "https://vimeo362227-23.onrender.com",
    "https://vimeo362227-24.onrender.com",
    "https://vimeo362227-25.onrender.com",
    "https://vimeo362227-26.onrender.com",
    "https://vimeo362227-27.onrender.com",
    "https://vimeo362227-28.onrender.com",
    "https://vimeo362227-29.onrender.com",
    "https://vimeo362227-30.onrender.com",
    "https://vimeo362227-31.onrender.com",
    "https://vimeo362227-32.onrender.com",
    "https://vimeo362227-33.onrender.com",
    "https://vimeo362227-34.onrender.com",
    "https://vimeo362227-35.onrender.com",
    "https://vimeo362227-36.onrender.com",
    "https://vimeo362227-37.onrender.com",
    "https://vimeo362227-38.onrender.com",
    "https://vimeo362227-39.onrender.com",
    "https://vimeo362227-40.onrender.com",
    "https://vimeo362227-41.onrender.com",
    "https://vimeo362227-42.onrender.com",
    "https://vimeo362227-43.onrender.com",
    "https://vimeo362227-44.onrender.com",
    "https://vimeo362227-45.onrender.com",
    "https://vimeo362227-46.onrender.com",
    "https://vimeo362227-47.onrender.com",
    "https://vimeo362227-48.onrender.com",
    "https://vimeo362227-49.onrender.com",
    "https://vimeo362227-50.onrender.com",
    "https://vimeo362227-51.onrender.com",
    "https://vimeo362227-52.onrender.com",
    "https://vimeo362227-53.onrender.com"
    "https://ellie001.onrender.com",
    "https://ellie002.onrender.com",
    "https://ellie003.onrender.com",
    "https://ellie004.onrender.com",
    "https://ellie006.onrender.com",
    "https://ellie005.onrender.com",
    "https://ellie010.onrender.com",
    "https://ellie007.onrender.com",
    "https://ellie008.onrender.com",
    "https://ellie009.onrender.com",
    "https://kai005.onrender.com",
    "https://kai006.onrender.com"
    
    "https://bcxdxrdqx-manyapps-001.onrender.com",
    "https://bcxdxrdqx-manyapps-002.onrender.com",
    "https://bcxdxrdqx-manyapps-003.onrender.com",
    "https://bcxdxrdqx-manyapps-004.onrender.com",
    "https://bcxdxrdqx-manyapps-005.onrender.com",
    "https://bcxdxrdqx-manyapps-006.onrender.com",
    "https://bcxdxrdqx-manyapps-007.onrender.com",
    "https://bcxdxrdqx-manyapps-008.onrender.com",
    "https://bcxdxrdqx-manyapps-009.onrender.com",
    "https://bcxdxrdqx-manyapps-010.onrender.com",
    "https://bcxdxrdqx-manyapps-011.onrender.com",
    "https://bcxdxrdqx-manyapps-012.onrender.com",
    "https://bcxdxrdqx-manyapps-013.onrender.com",
    "https://bcxdxrdqx-manyapps-014.onrender.com",
    "https://bcxdxrdqx-manyapps-015.onrender.com",
    "https://bcxdxrdqx-manyapps-016.onrender.com",
    "https://bcxdxrdqx-manyapps-017.onrender.com",
    "https://bcxdxrdqx-manyapps-018.onrender.com",
    "https://bcxdxrdqx-manyapps-019.onrender.com",
    "https://bcxdxrdqx-manyapps-020.onrender.com",  
    
    "https://uflulnjoaurhdhk-manyapps-001.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-002.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-003.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-004.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-005.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-006.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-007.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-008.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-009.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-010.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-011.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-012.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-013.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-014.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-015.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-016.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-017.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-018.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-019.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-020.onrender.com",  
    
    "https://kobpiwpwprfnj-manyapps-001.onrender.com",
    "https://kobpiwpwprfnj-manyapps-002.onrender.com",
    "https://kobpiwpwprfnj-manyapps-003.onrender.com",
    "https://kobpiwpwprfnj-manyapps-004.onrender.com",
    "https://kobpiwpwprfnj-manyapps-005.onrender.com",
    "https://kobpiwpwprfnj-manyapps-006.onrender.com",
    "https://kobpiwpwprfnj-manyapps-007.onrender.com",
    "https://kobpiwpwprfnj-manyapps-008.onrender.com",
    "https://kobpiwpwprfnj-manyapps-009.onrender.com",
    
    "https://resignation1-manyapps-001.onrender.com",
    "https://resignation1-manyapps-002.onrender.com",
    "https://resignation1-manyapps-003.onrender.com",
    "https://resignation1-manyapps-004.onrender.com",
    "https://resignation1-manyapps-005.onrender.com",
    "https://resignation1-manyapps-006.onrender.com",
    "https://resignation1-manyapps-007.onrender.com",
    "https://resignation1-manyapps-008.onrender.com",
    "https://resignation1-manyapps-009.onrender.com",
    "https://resignation1-manyapps-010.onrender.com",
    "https://resignation1-manyapps-011.onrender.com",
    "https://resignation1-manyapps-012.onrender.com",
    "https://resignation1-manyapps-013.onrender.com",
    "https://resignation1-manyapps-014.onrender.com",
    "https://resignation1-manyapps-015.onrender.com",
    "https://resignation1-manyapps-016.onrender.com",
    "https://resignation1-manyapps-017.onrender.com",
    "https://resignation1-manyapps-018.onrender.com",
    "https://resignation1-manyapps-019.onrender.com",
    "https://resignation1-manyapps-020.onrender.com",
]
'''

while True:
    # 记录成功的链接
    successful_urls = []

    def request_url(url):
        retry = 0
        while True:
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    print(f'{url} returned 200')
                    successful_urls.append(url)
                    return None  # 返回None表示成功
                else:
                    print(f'{url} returned {response.status_code}')
                    if retry < 5:
                        retry += 1
                        print(f'{url} retrying {retry}/5')
                    else:
                        break
            except requests.exceptions.RequestException as e:
                print(f'{url} failed: {e}')
                if retry < 6:
                    retry += 1
                    print(f'{url} retrying {retry}/6')
                else:
                    break
            time.sleep(1)  # 等待1秒后重试

    # 使用线程池并发请求
    with ThreadPoolExecutor(max_workers=80) as executor:
        futures = [executor.submit(request_url, url) for url in urls]
        # 等待所有请求完成
        for _ in as_completed(futures):
            pass

    # 将成功的链接写入文件
    if len(successful_urls) >= 50:
        with open('/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/urls.txt', 'w') as f:
            for url in successful_urls:
                f.write(url + '\n')
    else:
        print('Successful URLs less than 40, skipped writing to file.')

    # 如果所有链接都成功，则退出循环
    if set(successful_urls) == set(urls):
        print("All URLs succeeded!")
        break

    # 休眠一段时间后再次尝试
    print("一轮结束")
    print(len(successful_urls))
    time.sleep(5)
    os.system('clear')
