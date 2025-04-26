
from django import urls
from wagtail import blocks


class AffiliateLinkBlock(blocks.StructBlock):
    affiliate = blocks.PageChooserBlock(
        target_model='autoblog_affiliates.Affiliate')
    product_name = blocks.CharBlock()

    def render(self, value, context=None):
        url = urls.reverse('affiliate_click') + \
            f"?affiliate_id={value['affiliate'].id}&product={value['product_name']}"
        return f'<a href="{url}">{value["product_name"]}</a>'
