import publicWidget from '@web/legacy/js/public/public_widget';


publicWidget.registry.business_subscription_product = publicWidget.Widget.extend({
    selector: '.o_wsale_product_page',
    events: {
                // auto display server specifications based on Type numbers
                'click li.o_variant_pills': 'handle_server_specifications'
            },
    init() 
    {
        this._super(...arguments);
        $("li[data-attribute_name=Processor] select").prop('disabled', 'disabled');
        $("li[data-attribute_name=RAM] select").prop('disabled', 'disabled');
        $("li[data-attribute_name=SSD] select").prop('disabled', 'disabled'); 
        
        $("input[data-attribute_name=Type]").closest('li').find('.badge .oe_currency_value').each(function(){
            var price = $(this).text();  
            $(this).text(String(price)+String(' /m'));
        });
        
        $("input[data-attribute_name=Subscription]").closest('li').find('.badge .oe_currency_value').each(function(){
            var price = $(this).text();  
            $(this).text(String(price)+String(' /m'));
        });        
        
    },
    handle_server_specifications(event)
    {
        var o_variant_pills = $(event.currentTarget);
            var variant = o_variant_pills.find('input');
            if(variant.attr('data-attribute_name') == 'Type')
            {
                $("li[data-attribute_name=Processor] select option").removeAttr('selected');
                $("li[data-attribute_name=RAM] select option").removeAttr('selected');
                $("li[data-attribute_name=SSD] select option").removeAttr('selected');                console.log(variant.attr('data-value_name'))
                if(variant.attr('data-value_name')=='CPX21')
                {
                    $("li[data-attribute_name='Processor'] select option[data-value_name='3 Cores']").prop('selected', 'selected');
                    $("li[data-attribute_name='RAM'] select option[data-value_name='4Gi']").prop('selected', 'selected');
                    $("li[data-attribute_name='SSD'] select option[data-value_name='80Gi']").prop('selected', 'selected');
                }
                else if(variant.attr('data-value_name')=='CPX31')
                {
                    $("li[data-attribute_name='Processor'] select option[data-value_name='4 Cores']").prop('selected', 'selected');
                    $("li[data-attribute_name='RAM'] select option[data-value_name='8Gi']").prop('selected', 'selected');
                    $("li[data-attribute_name='SSD'] select option[data-value_name='160Gi']").prop('selected', 'selected');
                }
                else if(variant.attr('data-value_name')=='CPX41')
                {
                    $("li[data-attribute_name='Processor'] select option[data-value_name='8 Cores']").prop('selected', 'selected');
                    $("li[data-attribute_name='RAM'] select option[data-value_name='16Gi']").prop('selected', 'selected');
                    $("li[data-attribute_name='SSD'] select option[data-value_name='240Gi']").prop('selected', 'selected');
                }
                else if (variant.attr('data-value_name')=='CPX51')
                {
                    $("li[data-attribute_name='Processor'] select option[data-value_name='16 Cores']").prop('selected', 'selected');
                    $("li[data-attribute_name='RAM'] select option[data-value_name='32Gi']").prop('selected', 'selected');
                    $("li[data-attribute_name='SSD'] select option[data-value_name='360Gi']").prop('selected', 'selected');
                }
            }
    }
});

publicWidget.registry.business_subscription = publicWidget.Widget.extend({
    selector: '.homepage',
    events: {
                "click a.beginner-subscription": "beginner_subscription",
                "click a.professional-subscription": "professional_subscription",
                "click a.expert-subscription": "expert_subscription"
            },
    init() {
        this._super(...arguments);
    },
    beginner_subscription: function(){
        var subscription_type =  $('input#subscription-type').val();
        var _version = $("select#beginner-subscription").val();
        var _url = ''
        if(_version=='18')
        {
            _url = '/shop/odoo-18-0-community-9#attribute_values=0,0,0,0,0,23';
            if (subscription_type=='enterprise')
            {
                _url = '/shop/odoo-18-0-enterprise-17#attribute_values=0,0,0,0,0,23'; 
            }
        }
        if(_version=='17')
        {
            _url = '/shop/odoo-17-0-community-5#attribute_values=0,0,0,0,0,23';
            if (subscription_type=='enterprise')
                {
                    _url = '/shop/odoo-17-0-enterprise-18#attribute_values=0,0,0,0,0,23'; 
                }
        }
        else if(_version=='16')
        {
            _url = '/shop/product/odoo-16-0-community-11#attribute_values=0,0,0,0,0,23';
            if (subscription_type=='enterprise')
                {
                    _url = '/shop/odoo-18-0-enterprise-19#attribute_values=0,0,0,0,0,23'; 
                }
        }
        else if(_version=='15')
        {
            _url = '/shop/product/odoo-15-0-community-12#attribute_values=0,0,0,0,0,23';
        }
        else if(_version=='14')
        {
            _url = '/shop/product/odoo-14-0-community-14#attribute_values=0,0,0,0,0,23';
        }
        else if(_version=='13')
        {
            _url = '/shop/product/odoo-13-0-comunity-13#attribute_values=0,0,0,0,0,23';
        }
        else if(_version=='12')
        {
            _url = '/shop/product/odoo-12-0-comunity-15#attribute_values=0,0,0,0,0,23';
        }
        else if(_version=='11')
        {
            _url = '/shop/product/odoo-11-0-community-16#attribute_values=0,0,0,0,0,23';
        }
        window.open(
            _url,
        );
    },
    professional_subscription: function()
    {
        var subscription_type =  $('input#subscription-type').val();
        var _version = $("select#professional-subscription").val();
        var _url = ''
        if(_version=='18')
        {
            _url = '/shop/odoo-18-0-community-9#attribute_values=0,0,0,0,0,24';
            if (subscription_type=='enterprise')
                {
                    _url = '/shop/odoo-18-0-enterprise-17#attribute_values=0,0,0,0,0,24'; 
                }
        }
        if(_version=='17')
        {
            _url = '/shop/odoo-17-0-community-5#attribute_values=0,0,0,0,0,24';
            if (subscription_type=='enterprise')
                {
                    _url = '/shop/odoo-17-0-enterprise-18#attribute_values=0,0,0,0,0,24'; 
                }
        }
        else if(_version=='16')
        {
            _url = '/shop/product/odoo-16-0-community-11#attribute_values=0,0,0,0,0,24';
            if (subscription_type=='enterprise')
                {
                    _url = '/shop/odoo-16-0-enterprise-19#attribute_values=0,0,0,0,0,24'; 
                }
        }
        else if(_version=='15')
        {
            _url = '/shop/product/odoo-15-0-community-12#attribute_values=0,0,0,0,0,24';
        }
        else if(_version=='14')
        {
            _url = '/shop/product/odoo-14-0-community-14#attribute_values=0,0,0,0,0,24';
        }
        else if(_version=='13')
        {
            _url = '/shop/product/odoo-13-0-comunity-13#attribute_values=0,0,0,0,0,24';
        }
        else if(_version=='12')
        {
            _url = '/shop/product/odoo-12-0-comunity-15#attribute_values=0,0,0,0,0,24';
        }
        else if(_version=='11')
        {
            _url = '/shop/product/odoo-11-0-comunity-16#attribute_values=0,0,0,0,0,24';
        }
        window.open(
            _url,
        );
    },
    expert_subscription:function()
    {
        var subscription_type =  $('input#subscription-type').val();
        var _version = $("select#expert-subscription").val();
        var _url = ''
        if(_version=='18')
        {
            _url = '/shop/odoo-18-0-community-9#attribute_values=0,0,0,0,0,25';
            if (subscription_type=='enterprise')
                {
                    _url = '/shop/odoo-18-0-enterprise-17#attribute_values=0,0,0,0,0,25'; 
                }
        }
        if(_version=='17')
        {
            _url = '/shop/odoo-17-0-community-5#attribute_values=0,0,0,0,0,25';
            if (subscription_type=='enterprise')
                {
                    _url = '/shop/odoo-17-0-enterprise-18#attribute_values=0,0,0,0,0,25'; 
                }
        }
        else if(_version=='16')
        {
            _url = '/shop/product/odoo-16-0-comunity-11#attribute_values=0,0,0,0,0,25';
            if (subscription_type=='enterprise')
                {
                    _url = '/shop/odoo-16-0-enterprise-19#attribute_values=0,0,0,0,0,25'; 
                }
        }
        else if(_version=='15')
        {
            _url = 'shop/product/odoo-15-0-community-12#attribute_values=0,0,0,0,0,25';
        }
        else if(_version=='14')
        {
            _url = '/shop/product/odoo-14-0-community-14#attribute_values=0,0,0,0,0,25';
        }
        else if(_version=='13')
        {
            _url = '/shop/product/odoo-13-0-comunity-13#attribute_values=0,0,0,0,0,25';
        }
        else if(_version=='12')
        {
            _url = '/shop/product/odoo-12-0-comunity-15#attribute_values=0,0,0,0,0,25';
        }
        else if(_version=='11')
        {
            _url = '/shop/product/odoo-11-0-community-16#attribute_values=0,0,0,0,0,25';
        }
        window.open(
            _url,
        );
    }
});